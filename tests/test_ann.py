import json
from pathlib import Path
import tempfile
from threading import Lock
import time
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from anaxia.ann.core import Runner, Store
from anaxia.ann.hodge import cm_product_check, divisor_degree_threshold, power_check
from anaxia.ann.papers import export, research_summary
from anaxia.ann.spec import normalize
from anaxia.ann.thermal import (free_oscillator_obstruction, verify_block_trace, verify_seam_clusters,
                                verify_seam_endpoints, verify_thermal_batch)
from anaxia.ann.workers import execute, read_routes


class AnnTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.store = Store(self.directory / "ann.sqlite3")

    def make(self, **options):
        return self.store.create(normalize(dict(template_id="polynomial-demo", **options)))

    def test_10000_profiles_paginate_without_claiming_they_all_ran(self):
        mission = self.make(agent_count=10_000, max_tasks=7)
        last = self.store.snapshot(mission["id"], offset=9_998)
        self.assertEqual(last["counts"], {"dormant": 9993, "queued": 7})
        self.assertEqual([a["index"] for a in last["agents"]], [9998, 9999])
        self.assertIsNone(last["next_offset"])
        self.assertEqual(last["mission"]["model_calls_reserved"], 0)

    def test_concurrent_runner_and_model_budget(self):
        mission = self.make(agent_count=30, max_tasks=20, concurrency=4, mode="model",
                            max_model_calls=3, modelconfig={"model": "test"})
        mid = mission["id"]
        lock = Lock()
        active = 0
        peak = 0
        calls = 0

        def worker(_, claim):
            nonlocal active, peak, calls
            with lock:
                active += 1
                peak = max(peak, active)
                calls += claim["use_model"]
            time.sleep(0.01)
            with lock:
                active -= 1
            return {"summary": "Counter recorded."}

        runner = Runner(self.store, worker)
        self.store.control(mid, "start")
        state = runner.run(mid)
        self.assertEqual(state["counts"], {"completed": 20, "dormant": 10})
        self.assertGreater(peak, 1)
        self.assertLessEqual(peak, 4)
        self.assertEqual(calls, 3)
        self.assertEqual(state["mission"]["model_calls_reserved"], 3)

    def test_pause_and_reservation_survive_reopen(self):
        mission = self.make(agent_count=6, max_tasks=4, concurrency=2, mode="model",
                            max_model_calls=1, modelconfig={"model": "test"})
        mid = mission["id"]
        self.store.control(mid, "start")
        claim = self.store.claim(mid)
        self.assertTrue(claim["use_model"])
        self.store.control(mid, "pause")
        self.assertIsNone(self.store.claim(mid))
        with self.store.connect(write=True) as db:
            db.execute("UPDATE jobs SET lease=0 WHERE mission=? AND slot=?", (mid, claim["slot"]))
        reopened = Store(self.store.path)
        self.assertEqual(reopened.recover(mid), 1)
        self.assertFalse(reopened.complete(mid, claim, {"summary": "Late result."}))
        reopened.control(mid, "resume")
        self.assertFalse(reopened.claim(mid)["use_model"])
        reopened.control(mid, "cancel")
        self.assertEqual(reopened.snapshot(mid)["counts"], {"cancelled": 3, "dormant": 2, "failed": 1})
        self.assertEqual(reopened.mission(mid)["model_calls_reserved"], 1)

    def test_asynchronous_runner_can_restart_after_pausing(self):
        first = self.make(agent_count=2, max_tasks=2)
        second = self.make(agent_count=1)
        runner = Runner(self.store, lambda *_: {"summary": "Done"})
        runner.start(first["id"])
        deadline = time.monotonic() + 5
        while runner.thread and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(self.store.mission(first["id"])["status"], "completed")
        runner.start(second["id"])
        deadline = time.monotonic() + 5
        while runner.thread and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(self.store.mission(second["id"])["status"], "completed")

    def test_gate_rejects_proofs_for_a_different_statement(self):
        first = self.make(agent_count=1)
        real = execute(first, {"strategy": "exact-sturm", "slot": 0, "use_model": False})
        self.assertEqual(real["status"], "exact_univariate_verified")
        self.assertEqual(research_summary(first, [real])[0], "formal task verified")
        hodge = dict(normalize({"template_id": "hodge"}), id="test", status="completed")
        self.assertEqual(research_summary(hodge, [real])[0], "unresolved")
        real["report"]["task"]["domain"] = {"kind": "integer_box", "bounds": [[0, 1]]}
        self.assertEqual(research_summary(first, [real])[0], "unresolved")

    def test_model_vote_cannot_close_hodge_and_zip_is_readable(self):
        hodge = dict(normalize({"template_id": "hodge", "author": r"A&B \input{secret}",
                                "mode": "model", "max_model_calls": 1,
                                "modelconfig": {"model": "stub"}}), id="test", status="completed")
        with patch("anaxia.ann.workers.providers.propose", return_value={"proposal": "The conjecture is solved."}):
            finding = execute(hodge, {"strategy": "hodge-cycles", "slot": 0, "use_model": True})
        self.assertEqual(finding["status"], "checked_subresult")
        self.assertEqual(finding["proposal"], "The conjecture is solved.")
        result = export(hodge, [finding], self.directory)
        self.assertEqual(result["status"], "unresolved")
        with ZipFile(Path(result["directory"]) / "mission.zip") as bundle:
            self.assertIsNone(bundle.testzip())
            self.assertIn("vault/hodge-cycles.md", bundle.namelist())
            self.assertIn(r"A\&B \textbackslash{}input\{secret\}", bundle.read("main.tex").decode())
            certificate = json.loads(bundle.read("evidence.json"))
            self.assertEqual(certificate["checked_reports"], [])

    def test_rejects_task_replacement_and_unsafe_configurations(self):
        for spec in [
            {"agent_count": 10_001}, {"concurrency": True}, {"exploration": "jailbreak"},
            {"statement": "A different mathematical claim."},
            {"mode": "model", "max_model_calls": 1, "modelconfig": {"model": "m", "api_key": "secret"}},
            {"mode": "model", "max_model_calls": 1, "modelconfig": {
                "model": "m", "provider": "openai-compatible", "base_url": "https://example.org/v1"}},
        ]:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                normalize(dict(template_id="polynomial-demo", **spec))

    def test_open_gluon_route_data_is_selected_as_source_text(self):
        atlas = self.directory / "construction-atlas.json"
        atlas.write_text(json.dumps({"routes":[{"name":"Hodge cycle"}, {"name":"Other"}]}), encoding="utf-8")
        found = read_routes(atlas, "hodge")
        self.assertEqual(len(found), 1)
        self.assertIn("Hodge", found[0])

    def test_failed_model_keeps_checked_subresult_and_reports_error(self):
        mission = normalize({"template_id": "yang-mills", "exploration": "wide", "mode": "model",
                             "max_model_calls": 1, "modelconfig": {"model": "stub"}})
        self.assertIn("limit-audit", mission["strategies"])
        with patch("anaxia.ann.workers.providers.propose", side_effect=ValueError("Inference unavailable")) as call:
            finding = execute(mission, {"strategy": "ym-spectrum", "slot": 2, "use_model": True,
                                        "prior_findings": ["Compare the positive measures."]})
        self.assertEqual(call.call_args.args[0]["prior_worker_notes_for_review"], ["Compare the positive measures."])
        self.assertEqual(finding["status"], "checked_subresult")
        self.assertIn("exact moment equalities", finding["finding"])
        self.assertEqual(finding["model_error"], "Inference unavailable")
        self.assertFalse(finding["model_used"])
        self.assertEqual(research_summary(mission, [finding])[2]["ym-spectrum"]["model_errors"], 1)

    def test_hodge_divisor_products_span_in_the_example_family(self):
        self.assertEqual([power_check(n) for n in range(1, 5)],
                         [(1,), (4, 1), (9, 9, 1), (16, 36, 16, 1)])
        mission = normalize({"template_id": "hodge"})
        finding = execute(mission, {"strategy": "hodge-cycles",
                                    "slot": 3 * len(mission["strategies"]), "use_model": False})
        self.assertEqual(finding["status"], "checked_subresult")
        self.assertIn("(16, 36, 16, 1)", finding["finding"])
        self.assertEqual(research_summary(mission, [finding])[0], "unresolved")

    def test_mixed_cm_ranks_and_sharp_degree(self):
        self.assertEqual(cm_product_check(((2, 2), (3, 2), (6, 1))), (9, 26, 26, 9, 1))
        self.assertEqual([divisor_degree_threshold(d) for d in (-4, -23, -163)], [2, 5, 13])
        with self.assertRaises(ValueError):
            cm_product_check(((2, 1), (8, 1)))

    def test_thermal_route_checks_rational_seed_and_sharp_equalities(self):
        for batch in range(16):
            verify_thermal_batch(batch)
        mission = normalize({"template_id": "yang-mills"})
        finding = execute(mission, {"strategy": "ym-thermal", "slot": 0, "use_model": False})
        self.assertEqual(finding["status"], "checked_subresult")
        self.assertEqual(research_summary(mission, [finding])[0], "unresolved")

    def test_replica_endpoints_and_massless_control(self):
        for batch in range(32):
            verify_seam_endpoints(batch)
        control, seed = free_oscillator_obstruction()
        self.assertGreater(control, 1000 * seed)
        mission = normalize({"template_id": "yang-mills", "exploration": "wide"})
        for strategy in ("ym-seams", "ym-gaussian"):
            finding = execute(mission, {"strategy": strategy, "slot": 0, "use_model": False})
            self.assertEqual(finding["status"], "checked_subresult")
            self.assertEqual(research_summary(mission, [finding])[0], "unresolved")

    def test_construction_replays(self):
        for batch in (0, 5, 31):
            verify_block_trace(batch)
            verify_seam_clusters(batch)

    def test_focus_keeps_the_target_and_reaches_model(self):
        mission = normalize({"template_id": "yang-mills", "brief": "Control the large-field terminal remainder.",
                             "mode": "model", "max_model_calls": 1, "modelconfig": {"model": "stub"}})
        self.assertIn("compact simple gauge group", mission["statement"])
        with patch("anaxia.ann.workers.providers.propose", return_value={"proposal": "A proposed method."}) as call:
            finding = execute(mission, {"strategy": "ym-seam-clusters", "slot": 0, "use_model": True})
        self.assertEqual(call.call_args.args[0]["research_brief"], mission["brief"])
        self.assertEqual(research_summary(mission, [finding])[0], "unresolved")

    def test_model_context_research_and_critique(self):
        mission = self.store.create(normalize({"template_id": "yang-mills", "agent_count": 3, "max_tasks": 3,
                                               "strategy_ids": ["ym-rg", "ym-seams", "critique"], "concurrency": 1,
                                               "mode": "model", "max_model_calls": 3,
                                               "modelconfig": {"model": "stub"}}))
        contexts = {}

        def worker(_, claim):
            route = claim["strategy"]
            contexts[route] = claim["prior_findings"]
            return {"strategy": route, "finding": route}

        self.store.control(mission["id"], "start")
        Runner(self.store, worker).run(mission["id"])
        self.assertEqual(contexts["ym-seams"], [])
        self.assertEqual(contexts["critique"], ["ym-seams", "ym-rg"])
