#!/usr/bin/env python3
"""Contract tests for the SkillNet E4 fuzzy-language experiment."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SKILLNET_DIR = ROOT / "experiments" / "skillnet"
E4_DIR = SKILLNET_DIR / "e4"
RUNNER_PATH = SKILLNET_DIR / "run_condition.py"
VERIFY_PATH = SKILLNET_DIR / "verify_condition.py"
VALIDATOR_PATH = E4_DIR / "validate_e4_prompts.py"


def load_module(name: str, path: Path):
    if not path.is_file():
        raise AssertionError(f"missing required module: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load_module("skillnet_e4_runner", RUNNER_PATH)
sys.modules["run_condition"] = runner
verifier = load_module("skillnet_e4_verifier", VERIFY_PATH)


TASK_IDS = [
    "GT01_SINGLE",
    "GT02_FIN_GOAL",
    "GT03_PROC_GOAL",
    "GT04_TECH_GOAL",
    "GT05_BUS_GOAL",
    "GT06_HR_GOAL",
    "GT07_CROSS_CUSTOM_TECH_SUPPLIER",
    "GT08_CROSS_TECH_DELIVERY_PAYMENT",
    "GT09_CROSS_BUS_SERVICE_PAYMENT",
    "GT10_CROSS_ONBOARDING_EQUIPMENT",
    "GT11_CROSS_RECRUIT_BUDGET_OFFER",
    "GT12_CROSS_BUSINESS_TO_PO",
    "GT13_CROSS_INTERNAL_DEV_STAFF_DATA",
    "GT14_CROSS_PAYMENT_PERFORMANCE",
    "GT15_CROSS_SUPPLIER_CONTRACT_PO",
    "GT16_SPECIAL_SUPPLIER_FAIL",
    "GT17_SPECIAL_INVALID_INVOICE",
    "GT18_SPECIAL_BUILD_OR_BUY",
    "GT19_NO_TOOL_CLEAR",
    "GT20_NO_TOOL_FINANCE",
    "GT21_NO_TOOL_PROC",
]


def perfect_predictions() -> dict[str, dict[str, object]]:
    path = (
        ROOT
        / "SkillNet_Gold_Tasks_V4"
        / "evaluation"
        / "fixtures"
        / "gold_perfect_predictions.jsonl"
    )
    return {
        record["task_id"]: record
        for record in (
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


class E4ResolverTests(unittest.TestCase):
    def test_e4_accepts_only_size_46(self) -> None:
        with self.assertRaisesRegex(ValueError, "E4 is fixed to size 46"):
            runner.resolve_condition(ROOT, "E4", "A", 30)

    def test_e4_resolver_returns_all_canonical_task_ids(self) -> None:
        catalogue_path, catalogue, task_ids = runner.resolve_condition(
            ROOT, "E4", "A", 46
        )

        self.assertEqual(task_ids, TASK_IDS)
        self.assertEqual(catalogue["configuration"], "A")
        self.assertEqual(catalogue_path.name, "A_flat_catalogue.json")
        prompts = runner.load_prompt_map(ROOT, "E4")
        self.assertEqual(list(prompts), TASK_IDS)
        self.assertTrue(
            all(record["source"].startswith("experiments/skillnet/e4/prompts/")
                for record in prompts.values())
        )

    def test_e4_rejects_resume_instead_of_replacing_answers(self) -> None:
        argv = [
            str(RUNNER_PATH),
            "--experiment",
            "E4",
            "--configuration",
            "A",
            "--size",
            "46",
            "--run-id",
            "no_resume",
            "--execute",
            "--resume",
        ]
        with patch.object(sys, "argv", argv):
            with self.assertRaisesRegex(SystemExit, "E4 does not allow --resume"):
                runner.main()


class E4PromptValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module("skillnet_e4_validator", VALIDATOR_PATH)
        cls.manifest = json.loads(
            (E4_DIR / "E4_prompt_manifest.json").read_text(encoding="utf-8")
        )
        cls.gold = json.loads(
            (
                ROOT
                / "SkillNet_Gold_Tasks_V4"
                / "02_Gold_Standard_21_V4.json"
            ).read_text(encoding="utf-8")
        )

    def test_exactly_21_e4_prompts_exist_and_validate(self) -> None:
        paths = sorted((E4_DIR / "prompts").glob("GT*.txt"))
        self.assertEqual(len(paths), 21)

        report = self.validator.validate_repository(ROOT)

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual([row["task_id"] for row in report["tasks"]], TASK_IDS)
        self.assertTrue(all(row["status"] == "PASS" for row in report["tasks"]))

    def test_validator_rejects_canonical_skill_id_leakage(self) -> None:
        errors = self.validator.validate_prompt_text(
            "请处理这件事并调用 procurement-supplier-selection。",
            self.gold["tasks"][0],
            self.gold,
        )
        self.assertIn("canonical_skill_id_leakage", {item["code"] for item in errors})

    def test_validator_rejects_explicit_step_enumeration(self) -> None:
        errors = self.validator.validate_prompt_text(
            "先找供应商，然后核对资质，最后选出一家。",
            self.gold["tasks"][2],
            self.gold,
        )
        self.assertIn("explicit_step_enumeration", {item["code"] for item in errors})

    def test_validator_rejects_more_than_two_sentences(self) -> None:
        errors = self.validator.validate_prompt_text(
            "现状已明确。请推进目标。后续先不处理。",
            self.gold["tasks"][0],
            self.gold,
        )
        self.assertIn("sentence_count", {item["code"] for item in errors})

    def test_validator_rejects_missing_semantic_audit_fields(self) -> None:
        errors = self.validator.validate_audit_task({"task_id": "GT01_SINGLE"})
        self.assertIn("missing_audit_field", {item["code"] for item in errors})

    def test_validator_rejects_modified_gold_contract_hash(self) -> None:
        record = self.manifest["tasks"][0]
        changed = copy.deepcopy(self.gold["tasks"][0])
        changed["required_skills"] = []

        errors = self.validator.validate_semantic_contract(record, changed)

        self.assertIn(
            "semantic_contract_sha256_mismatch",
            {item["code"] for item in errors},
        )

    def test_a_b_c_share_identical_prompt_source_and_hash(self) -> None:
        sets = self.manifest["condition_prompt_sets"]
        self.assertEqual(set(sets), {"A", "B", "C"})
        self.assertEqual(
            {entry["prompt_source"] for entry in sets.values()},
            {"experiments/skillnet/e4/prompts"},
        )
        self.assertEqual(len({entry["prompt_set_sha256"] for entry in sets.values()}), 1)


class E4FixtureArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        temporary = Path(cls.temporary.name)
        cls.state_root = temporary / "state"
        fixture_dir = temporary / "fixtures"
        fixture_dir.mkdir()
        records = perfect_predictions()
        for task_id in TASK_IDS:
            (fixture_dir / f"{task_id}.txt").write_text(
                json.dumps(records[task_id], ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        runner_argv = [
            str(RUNNER_PATH),
            "--experiment",
            "E4",
            "--configuration",
            "B",
            "--size",
            "46",
            "--run-id",
            "e4_fixture_contract",
            "--fixture-response-dir",
            str(fixture_dir),
            "--state-root",
            str(cls.state_root),
        ]
        with patch.object(sys, "argv", runner_argv):
            cls.runner_exit = runner.main()
        verifier_argv = [
            str(VERIFY_PATH),
            "--experiment",
            "E4",
            "--configuration",
            "B",
            "--size",
            "46",
            "--run-id",
            "e4_fixture_contract",
            "--state-root",
            str(cls.state_root),
        ]
        with patch.object(sys, "argv", verifier_argv):
            cls.verifier_exit = verifier.main()
        cls.run_root = (
            cls.state_root
            / "runs"
            / "E4"
            / "B"
            / "size_46"
            / "e4_fixture_contract"
        )
        cls.result_root = (
            cls.state_root
            / "results"
            / "E4"
            / "B"
            / "size_46"
            / "e4_fixture_contract"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_fixture_runner_and_verifier_create_21_complete_artifact_sets(self) -> None:
        self.assertEqual(self.runner_exit, 0)
        self.assertEqual(self.verifier_exit, 0)
        task_dirs = sorted(path.name for path in self.run_root.glob("GT*") if path.is_dir())
        self.assertEqual(task_dirs, TASK_IDS)
        required = set(runner.RUN_REQUIRED_ARTIFACTS) | set(
            verifier.VERIFIER_REQUIRED_ARTIFACTS
        ) | {"prediction.json"}
        for task_id in TASK_IDS:
            actual = {
                path.name
                for path in (self.run_root / task_id).iterdir()
                if path.is_file()
            }
            self.assertTrue(required <= actual, f"{task_id}: {sorted(required - actual)}")

    def test_verifier_uses_canonical_21_task_gold(self) -> None:
        manifest = json.loads(
            (self.result_root / "verification_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            manifest["gold_path"],
            "SkillNet_Gold_Tasks_V4/02_Gold_Standard_21_V4.json",
        )
        self.assertEqual(manifest["task_ids"], TASK_IDS)
        self.assertEqual(
            manifest["e4_prompt_manifest_sha256"],
            json.loads(
                (self.run_root / "condition_metadata.json").read_text(
                    encoding="utf-8"
                )
            )["e4_prompt_manifest_sha256"],
        )
        self.assertIn("e4_semantic_audit_sha256", manifest)

    def test_fixture_records_e4_prompt_provenance(self) -> None:
        condition = json.loads(
            (self.run_root / "condition_metadata.json").read_text(encoding="utf-8")
        )
        prompt_manifest = json.loads(
            (E4_DIR / "E4_prompt_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(condition["experiment"], "E4")
        self.assertIn("e4_prompt_manifest_sha256", condition)
        self.assertEqual(
            condition["prompt_set_sha256"],
            prompt_manifest["condition_prompt_sets"]["B"]["prompt_set_sha256"],
        )
        for task_id in TASK_IDS:
            packet = json.loads(
                (self.run_root / task_id / "packet_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(
                packet["inputs"]["task_prompt"]["source"].startswith(
                    "experiments/skillnet/e4/prompts/"
                )
            )

    def test_comparison_uses_formal_original_b_run_02(self) -> None:
        comparison = json.loads(
            (self.result_root / "e0_robustness_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(comparison["baseline"]["run_id"], "run_02")
        self.assertNotIn("PATCHED", json.dumps(comparison))
        self.assertEqual(comparison["configuration"], "B")
        self.assertEqual(len(comparison["task_transitions"]), 21)
        self.assertTrue(
            all(
                {
                    "e0_functional_success",
                    "e4_functional_success",
                    "functional_transition",
                    "e0_clean_success",
                    "e4_clean_success",
                    "clean_transition",
                }
                <= set(row)
                for row in comparison["task_transitions"]
            )
        )
        self.assertIn("functional_success", comparison["metrics"])
        self.assertIn("gold_constraint_violation_rate", comparison["metrics"])
        self.assertIsInstance(comparison["failure_tag_deltas"], list)


if __name__ == "__main__":
    unittest.main()
