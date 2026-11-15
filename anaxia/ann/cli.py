"""Run ann research missions, inspect the graph, and export evidence."""

import argparse
import json
from pathlib import Path
import sys

from .core import Runner, Store
from .papers import export, research_summary
from .server import make_server
from .spec import normalize
from .strategies import TARGETS, catalog
from .workers import execute


def emit(value):
    print(json.dumps(value, ensure_ascii=True, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/local/ann.sqlite3"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("strategies")
    sub.add_parser("list")
    create = sub.add_parser("run", help="Create and execute a bounded mission")
    source = create.add_mutually_exclusive_group(required=True)
    source.add_argument("--target", choices=TARGETS)
    source.add_argument("--spec", type=Path)
    create.add_argument("--agents", type=int)
    create.add_argument("--tasks", type=int)
    create.add_argument("--concurrency", type=int)
    create.add_argument("--exploration", choices=["focused", "wide"])
    create.add_argument("--export", type=Path, help="Write the paper bundle in this directory")
    create.add_argument("--pdf", action="store_true")
    resume = sub.add_parser("resume", help="Resume a paused or interrupted mission")
    resume.add_argument("mission")
    report = sub.add_parser("export", help="Recheck evidence and assemble a draft paper")
    report.add_argument("mission")
    report.add_argument("--output", type=Path, default=Path("data/local/ann-exports"))
    report.add_argument("--pdf", action="store_true")
    serve = sub.add_parser("serve", help="Open the local research graph")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--output", type=Path, default=Path("data/local/ann-exports"))
    args = parser.parse_args(argv)
    try:
        if args.command == "strategies":
            emit(catalog())
            return 0
        store = Store(args.db)
        runner = Runner(store, execute)
        if args.command == "list":
            emit({"missions": store.missions()})
        if args.command == "serve":
            if not 0 <= args.port <= 65_535:
                raise ValueError("Port must be from 0 to 65535")
            with make_server(store, runner, args.port, args.output) as server:
                print(f"ann research graph: http://127.0.0.1:{server.server_port}/", flush=True)
                server.serve_forever()
        if args.command == "export":
            emit(export(store.mission(args.mission), store.results(args.mission), args.output, pdf=args.pdf))
        if args.command in ("run", "resume"):
            if args.command == "run":
                raw = {"template_id": args.target}
                if args.spec:
                    with args.spec.open(encoding="utf-8-sig") as stream:
                        data = stream.read(48_001)
                    if len(data) > 48_000:
                        raise ValueError("Mission file exceeds its input limit")
                    raw = json.loads(data)
                    if not isinstance(raw, dict):
                        raise ValueError("Mission file must contain a JSON object")
                for key, value in (("agent_count", args.agents), ("max_tasks", args.tasks),
                                   ("concurrency", args.concurrency), ("exploration", args.exploration)):
                    if value is not None:
                        raw[key] = value
                mission = store.create(normalize(raw))
            else:
                mission = store.mission(args.mission)
            mid = mission["id"]
            print(f"Mission {mid}", file=sys.stderr, flush=True)
            store.control(mid, "resume" if mission["status"] == "paused" else "start")
            try:
                snapshot = runner.run(mid)
            except KeyboardInterrupt:
                if store.mission(mid)["status"] == "running":
                    store.control(mid, "pause")
                raise
            results = store.results(mid)
            conclusion, proofs, routes = research_summary(snapshot["mission"], results)
            value = {"id": mid, "status": snapshot["mission"]["status"], "counts": snapshot["counts"],
                     "conclusion": conclusion, "rechecked_certificates": len(proofs),
                     "strategies": {key: stats["count"] for key, stats in routes.items()},
                     "model_calls_reserved": snapshot["mission"]["model_calls_reserved"]}
            if getattr(args, "export", None):
                value["export"] = export(snapshot["mission"], results, args.export, pdf=args.pdf)
            emit(value)
        return 0
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, KeyError, RecursionError) as error:
        print(f"ann: {error}", file=sys.stderr)
        return 2
