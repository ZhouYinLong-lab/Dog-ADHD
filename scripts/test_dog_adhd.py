"""Pipeline checks use synthetic fixtures; they do not evaluate model behavior."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

import dog_adhd as app


class LocalTrialTests(unittest.TestCase):
    def setUp(self):
        work = (app.ROOT / "work").resolve()
        work.mkdir(exist_ok=True)
        self.assertTrue(work.is_relative_to(app.ROOT.resolve()))
        self.temp = tempfile.TemporaryDirectory(prefix="pipeline-test-", dir=work)
        self.base = Path(self.temp.name).resolve()
        self.assertTrue(self.base.is_relative_to(work))
        self.addCleanup(self.temp.cleanup)
        self.suite_path = self.base / "suite.json"
        app.write_json(self.suite_path, {
            "suite_id": "synthetic-fixture",
            "cases": [
                {"id": "case1", "scenario_id": "same-scene", "user_turns": ["问题一", "追问一"], "criteria": ["RUBRIC_SECRET_A"]},
                {"id": "case2", "scenario_id": "same-scene", "user_turns": ["问题二"], "criteria": ["RUBRIC_SECRET_B"]},
            ],
        })
        self.run = self.base / "run"
        self.manifest = app.prepare(self.run, self.suite_path, ["B", "v0.3"], repeats=2)

    def answer_records(self):
        records = app.read_jsonl(self.run / "answers-template.jsonl")
        for record in records:
            record.update(model="synthetic-fixture", context_note="Synthetic data; no model calls", settings={"seed": "not-applicable"})
            record["answers"] = [f"合成回答 {index} 中文" for index in range(len(record["answers"]))]
        return records

    def create_review(self):
        self.answers_path = self.base / "answers.jsonl"
        app.write_jsonl(self.answers_path, self.answer_records())
        return app.make_review(self.run, self.answers_path, "synthetic")

    def test_prompt_change_is_limited_to_e_and_skill_matches_source(self):
        previous, current = app.modules_for("0.2"), app.modules_for("0.3")
        for module in "FJW":
            self.assertEqual(previous[module], current[module])
        self.assertNotEqual(previous["E"], current["E"])
        target = app.build_skill("0.3", self.base / "skill")
        app.build_skill("0.3", self.base / "skill", check=True)
        self.assertIn(app.prompt("0.3"), target.read_text(encoding="utf-8"))

    def test_prepare_separates_rubric_and_keeps_multiturn_inputs(self):
        sessions = app.read_jsonl(self.run / "sessions.jsonl")
        self.assertNotIn("RUBRIC_SECRET", json.dumps(sessions))
        by_id = {record["session_id"]: record for record in sessions}
        for assignment in self.manifest["assignments"]:
            session = by_id[assignment["session_id"]]
            if assignment["condition"] == "B":
                self.assertEqual(session["system_prompt"], "")
            if assignment["case_id"] == "case1":
                self.assertEqual(session["user_turns"], ["问题一", "追问一"])
        self.assertEqual(self.manifest["planned_model_turns"], 12)

    def test_prepare_refuses_to_overwrite_existing_run(self):
        with self.assertRaisesRegex(ValueError, "exists"):
            app.prepare(self.run, self.suite_path, ["B", "v0.3"])

    def test_import_rejects_missing_duplicate_and_incomplete_turns(self):
        records = self.answer_records()
        invalid_batches = [records[:-1], records + [records[0]], copy.deepcopy(records)]
        invalid_batches[-1][0]["answers"] = []
        for invalid in invalid_batches:
            with self.subTest(size=len(invalid)), self.assertRaises(ValueError):
                app.validate_answers(invalid, self.manifest)

    def test_import_rejects_mixed_models_or_settings(self):
        records = self.answer_records()
        for field, value in (("model", "other-model"), ("settings", {"seed": 99})):
            invalid = copy.deepcopy(records)
            invalid[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                app.validate_answers(invalid, self.manifest)

    def test_blind_file_hides_conditions_and_roundtrips_answers(self):
        review = self.create_review()
        by_id = {r["session_id"]: r for r in app.read_jsonl(self.answers_path)}
        labels = app.read_json(self.run / "private/labels.json")
        for item in review["items"]:
            for candidate in item["candidates"]:
                self.assertNotIn("condition", candidate)
                self.assertNotIn("system_prompt", candidate)
                self.assertNotIn("model", candidate)
                self.assertEqual(candidate["answers"], by_id[labels[candidate["label"]]["session_id"]]["answers"])
        self.assertEqual(review["kind"], "synthetic")
        with self.assertRaisesRegex(ValueError, "exists"):
            app.make_review(self.run, self.answers_path, "synthetic")

    def test_unrated_table_is_not_a_pass(self):
        self.create_review()
        with self.assertRaisesRegex(ValueError, "No ratings"):
            app.summarize(self.run)

    def test_pair_counts_and_correlated_scenarios_are_preserved(self):
        review = self.create_review()
        labels = app.read_json(self.run / "private/labels.json")
        outcomes = {( "case1", 1): (False, False), ("case1", 2): (False, True), ("case2", 1): (True, False), ("case2", 2): (True, True)}
        for item in review["items"]:
            for candidate in item["candidates"]:
                condition = labels[candidate["label"]]["condition"]
                candidate["ratings"]["unnecessary_qualification"] = outcomes[item["case_id"], item["repeat"]][condition == "v0.3"]
                candidate["notes"] = "Synthetic outcome for pipeline counting; no model evidence."
        app.write_json(self.run / "review.json", review)
        report = app.summarize(self.run)
        self.assertEqual((report["cases"], report["scenarios"], report["sessions"]), (2, 1, 8))
        self.assertEqual(report["kind"], "synthetic")
        self.assertEqual(report["paired"][0]["metrics"]["unnecessary_qualification"], {
            "both_pass": 1, "right_regression": 1, "right_improvement": 1, "both_fail": 1, "unrated_pairs": 0,
        })
        self.assertEqual(report["scores"]["B"]["critical_failure"]["rated_sessions"], 0)

    def test_report_rejects_changed_answers_and_unknown_labels(self):
        review = self.create_review()
        for field, value in (("answers", ["changed"]), ("label", "unknown")):
            changed = copy.deepcopy(review)
            changed["items"][0]["candidates"][0][field] = value
            app.write_json(self.run / "review.json", changed)
            with self.subTest(field=field), self.assertRaises(ValueError):
                app.summarize(self.run)


if __name__ == "__main__":
    unittest.main()
