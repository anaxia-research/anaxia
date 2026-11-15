"""Durable, bounded research queue. Execution status is independent of proof status."""

import json
import sqlite3
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import closing, contextmanager
from pathlib import Path
from threading import Lock, Thread
from uuid import uuid4

MAX_AGENTS = 10_000
MAX_CONCURRENCY = 64
LEASE_SECONDS = 180
ACTIVE = ("queued", "running")


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=15)) as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS missions(
                    id TEXT PRIMARY KEY, spec TEXT NOT NULL, status TEXT NOT NULL,
                    created REAL NOT NULL, calls INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS jobs(
                    mission TEXT NOT NULL REFERENCES missions(id), slot INTEGER NOT NULL,
                    status TEXT NOT NULL, token TEXT, lease REAL, result TEXT,
                    PRIMARY KEY(mission, slot)
                );
                CREATE INDEX IF NOT EXISTS job_queue ON jobs(mission, status, slot);
                CREATE TABLE IF NOT EXISTS events(
                    id INTEGER PRIMARY KEY, mission TEXT NOT NULL REFERENCES missions(id),
                    kind TEXT NOT NULL, detail TEXT NOT NULL, created REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS mission_events ON events(mission, id);
            """)

    @contextmanager
    def connect(self, *, write=False):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=NORMAL")
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _mission(db, mid):
        row = db.execute("SELECT * FROM missions WHERE id=?", (mid,)).fetchone()
        if row is None:
            raise KeyError("Mission not found")
        return dict(json.loads(row["spec"]), id=mid, status=row["status"],
                    created_at=row["created"], model_calls_reserved=row["calls"])

    @staticmethod
    def _event(db, mid, kind, detail):
        db.execute("INSERT INTO events(mission,kind,detail,created) VALUES(?,?,?,?)",
                   (mid, kind, json.dumps(detail), time.time()))

    def create(self, spec):
        mid = uuid4().hex
        with self.connect(write=True) as db:
            db.execute("INSERT INTO missions VALUES(?,?,'queued',?,0)",
                       (mid, json.dumps(spec), time.time()))
            db.executemany("INSERT INTO jobs(mission,slot,status) VALUES(?,?,?)",
                           ((mid, slot, "queued" if slot < spec["max_tasks"] else "dormant")
                            for slot in range(spec["agent_count"])))
            self._event(db, mid, "created", {"agents": spec["agent_count"], "tasks": spec["max_tasks"]})
            return self._mission(db, mid)

    def mission(self, mid):
        with self.connect() as db:
            return self._mission(db, mid)

    def missions(self):
        with self.connect() as db:
            ids = db.execute("SELECT id FROM missions ORDER BY created DESC LIMIT 200").fetchall()
            return [self._mission(db, row["id"]) for row in ids]

    def _settle(self, db, mid):
        row = db.execute("SELECT status FROM missions WHERE id=?", (mid,)).fetchone()
        if row["status"] in ("running", "paused") and not db.execute(
            "SELECT 1 FROM jobs WHERE mission=? AND status IN ('queued','running') LIMIT 1", (mid,)
        ).fetchone():
            db.execute("UPDATE missions SET status='completed' WHERE id=?", (mid,))
            self._event(db, mid, "completed", {"message": "Scheduled work finished."})

    def control(self, mid, action):
        with self.connect(write=True) as db:
            mission = self._mission(db, mid)
            current = mission["status"]
            target = {"start": "running", "resume": "running", "pause": "paused", "cancel": "cancelled"}.get(action)
            allowed = {"start": {"queued", "running"}, "resume": {"paused", "running"},
                       "pause": {"running", "paused"}, "cancel": {"queued", "running", "paused", "cancelled"}}
            if target is None or current not in allowed[action]:
                raise ValueError(f"Action {action!r} is unavailable for a {current} mission")
            if current != target:
                db.execute("UPDATE missions SET status=? WHERE id=?", (target, mid))
                if action == "cancel":
                    db.execute("""UPDATE jobs SET status='cancelled', token=NULL, lease=NULL
                                  WHERE mission=? AND status IN ('queued','running')""", (mid,))
                self._event(db, mid, target, {"previous": current})
                self._settle(db, mid)
            return self._mission(db, mid)

    def recover(self, mid):
        with self.connect(write=True) as db:
            self._mission(db, mid)
            # A process may have sent a model request before it died. Preserve
            # its charged reservation and never silently replay that request.
            affected = db.execute("""UPDATE jobs SET status='failed', token=NULL, lease=NULL, result=?
                                     WHERE mission=? AND status='running' AND lease<?""",
                                  (json.dumps({"summary": "Worker lease expired. Request outcome is unknown."}),
                                   mid, time.time())).rowcount
            if affected:
                self._event(db, mid, "recovered", {"expired_jobs": affected})
                self._settle(db, mid)
            return affected

    def claim(self, mid):
        with self.connect(write=True) as db:
            mission = self._mission(db, mid)
            if mission["status"] != "running":
                return None
            if db.execute("SELECT count(*) FROM jobs WHERE mission=? AND status='running'",
                          (mid,)).fetchone()[0] >= mission["concurrency"]:
                return None
            row = db.execute("SELECT slot FROM jobs WHERE mission=? AND status='queued' ORDER BY slot LIMIT 1",
                             (mid,)).fetchone()
            if not row:
                self._settle(db, mid)
                return None
            token = uuid4().hex
            slot = row["slot"]
            use_model = mission["mode"] == "model" and mission["model_calls_reserved"] < mission["max_model_calls"]
            if use_model:
                db.execute("UPDATE missions SET calls=calls+1 WHERE id=?", (mid,))
            db.execute("UPDATE jobs SET status='running', token=?, lease=? WHERE mission=? AND slot=?",
                       (token, time.time() + LEASE_SECONDS, mid, slot))
            self._event(db, mid, "started", {"slot": slot, "model": use_model})
            return dict(slot=slot, id=f"{mid}:{slot}", token=token,
                        strategy=mission["strategies"][slot % len(mission["strategies"])], use_model=use_model)

    def recent_findings(self, mid):
        with self.connect() as db:
            rows = db.execute("""SELECT result FROM jobs WHERE mission=? AND status='completed'
                                 ORDER BY slot DESC LIMIT 12""", (mid,))
            findings = []
            for row in rows:
                result = json.loads(row["result"])
                text = result.get("proposal") or result.get("finding")
                if isinstance(text, str) and text[:700] not in findings:
                    findings.append(text[:700])
                    if len(findings) == 3:
                        break
            return findings

    def renew(self, mid, claims):
        with self.connect(write=True) as db:
            db.executemany("UPDATE jobs SET lease=? WHERE mission=? AND slot=? AND token=? AND status='running'",
                           ((time.time() + LEASE_SECONDS, mid, c["slot"], c["token"]) for c in claims))

    def complete(self, mid, claim, result, *, failed=False):
        data = json.dumps(result, ensure_ascii=True, allow_nan=False)
        if len(data) > 100_000:
            raise ValueError("Result exceeds its size budget")
        with self.connect(write=True) as db:
            status = "failed" if failed else "completed"
            count = db.execute("""UPDATE jobs SET status=?, result=?, lease=NULL, token=NULL
                                 WHERE mission=? AND slot=? AND token=? AND status='running'""",
                               (status, data, mid, claim["slot"], claim["token"])).rowcount
            if count:
                self._event(db, mid, "job_" + status,
                            {"slot": claim["slot"], "strategy": claim["strategy"],
                             "summary": (result.get("model_error") or result.get("summary", ""))[:300]})
                self._settle(db, mid)
            return bool(count)

    @staticmethod
    def _events(db, mid, after=None, limit=40):
        if after is None:
            rows = list(db.execute("SELECT * FROM events WHERE mission=? ORDER BY id DESC LIMIT ?", (mid, limit)))
            rows.reverse()
        else:
            rows = db.execute("SELECT * FROM events WHERE mission=? AND id>? ORDER BY id LIMIT ?", (mid, after, limit))
        return [dict(id=row["id"], kind=row["kind"], payload=json.loads(row["detail"]),
                     created_at=row["created"]) for row in rows]

    def events(self, mid, after):
        with self.connect() as db:
            self._mission(db, mid)
            return self._events(db, mid, after, 100)

    def snapshot(self, mid, offset=0, limit=512):
        with self.connect() as db:
            mission = self._mission(db, mid)
            rows = db.execute("""SELECT slot,status,result FROM jobs WHERE mission=?
                                 ORDER BY slot LIMIT ? OFFSET ?""", (mid, limit, offset))
            agents = []
            for row in rows:
                result = json.loads(row["result"]) if row["result"] else {}
                slot = row["slot"]
                agents.append(dict(id=f"{mid}:{slot}", index=slot, status=row["status"],
                                   strategy=mission["strategies"][slot % len(mission["strategies"])],
                                   result={key: result[key] for key in
                                           ("status", "summary", "finding", "scope", "proposal", "model_error")
                                           if key in result}))
            counts = dict(db.execute("SELECT status, count(*) FROM jobs WHERE mission=? GROUP BY status", (mid,)))
            events = self._events(db, mid)
            return dict(mission=mission, agents=agents, counts=counts, events=events,
                        cursor=events[-1]["id"] if events else 0, offset=offset,
                        next_offset=offset + len(agents) if offset + len(agents) < mission["agent_count"] else None)

    def results(self, mid):
        with self.connect() as db:
            self._mission(db, mid)
            return [dict(index=row["slot"], **json.loads(row["result"]))
                    for row in db.execute("SELECT slot,result FROM jobs WHERE mission=? AND result IS NOT NULL ORDER BY slot", (mid,))]


class Runner:
    """One active mission per coordinator. A bounded pool multiplexes its profiles."""
    def __init__(self, store, worker):
        self.store = store
        self.worker = worker
        self.lock = Lock()
        self.thread = None
        self.active_id = None

    def start(self, mid, action="start"):
        with self.lock:
            if self.thread and self.thread.is_alive() and self.active_id != mid:
                raise ValueError("Pause or finish the active mission before starting another")
            mission = self.store.control(mid, action)
            if not self.thread or not self.thread.is_alive():
                self.active_id = mid
                self.thread = Thread(target=self.run, args=(mid,), daemon=True)
                self.thread.start()
            return mission

    def run(self, mid):
        mission = self.store.mission(mid)
        futures = {}
        renew_at = time.monotonic() + 20
        with ThreadPoolExecutor(max_workers=mission["concurrency"]) as pool:
            while True:
                self.store.recover(mid)
                if time.monotonic() >= renew_at and futures:
                    self.store.renew(mid, futures.values())
                    renew_at = time.monotonic() + 20
                while len(futures) < mission["concurrency"]:
                    claim = self.store.claim(mid)
                    if not claim:
                        break
                    if claim["use_model"]:
                        claim["prior_findings"] = self.store.recent_findings(mid)
                    future = pool.submit(self.worker, mission, claim)
                    futures[future] = claim
                if not futures:
                    with self.lock:
                        if self.store.mission(mid)["status"] != "running":
                            if self.active_id == mid:
                                self.thread = None
                                self.active_id = None
                            break
                    time.sleep(0.25)
                    continue
                done, _ = wait(futures, timeout=0.25, return_when=FIRST_COMPLETED)
                for future in done:
                    claim = futures.pop(future)
                    try:
                        self.store.complete(mid, claim, future.result())
                    except Exception:
                        self.store.complete(mid, claim, {"summary": "Worker failed. Check its configuration and evidence."},
                                            failed=True)
        return self.store.snapshot(mid)
