#!/usr/bin/env python3
"""Fixture-only runner/verifier contract for SkillNet E1-v2."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
E1V2_DIR = ROOT / "experiments" / "skillnet_e1v2"


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = import_module("run_condition", E1V2_DIR / "run_condition.py")
evaluator = import_module("evaluate_e1v2", E1V2_DIR / "evaluate_e1v2.py")
verifier = import_module("verify_condition", E1V2_DIR / "verify_condition.py")


class E1V2ArtifactContractTests(unittest.TestCase):
    def test_fixture_dry_run_creates_all_21_complete_artifact_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_root = Path(temporary) / "state"
            runner_argv = [
                str(E1V2_DIR / "run_condition.py"),
                "--configuration",
                "A",
                "--size",
                "10",
                "--run-id",
                "fixture_dry_run",
                "--fixture-response-dir",
                str(E1V2_DIR / "fixtures" / "gold_perfect"),
                "--state-root",
                str(state_root),
            ]
            with patch.object(sys, "argv", runner_argv):
                self.assertEqual(0, runner.main())
            verifier_argv = [
                str(E1V2_DIR / "verify_condition.py"),
                "--configuration",
                "A",
                "--size",
                "10",
                "--run-id",
                "fixture_dry_run",
                "--state-root",
                str(state_root),
            ]
            with patch.object(sys, "argv", verifier_argv):
                self.assertEqual(0, verifier.main())

            run_root = (
                state_root
                / "runs"
                / "E1V2"
                / "A"
                / "size_10"
                / "fixture_dry_run"
            )
            result_root = (
                state_root
                / "results"
                / "E1V2"
                / "A"
                / "size_10"
                / "fixture_dry_run"
            )
            condition = json.loads(
                (run_root / "condition_validation.json").read_text(
                    encoding="utf-8"
                )
            )
            summary = json.loads(
                (result_root / "condition_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("complete", condition["status"])
            self.assertEqual(21, condition["task_count"])
            self.assertEqual(1.0, summary["strict_functional_success"])
            self.assertEqual(1.0, summary["semantic_functional_success"])
            self.assertEqual(1.0, summary["skill_routing_success"])
            self.assertEqual(1.0, summary["control_success"])
            self.assertEqual(
                0,
                summary["consistency_counts"][
                    "semantic_true_skill_routing_false"
                ],
            )
            self.assertEqual(
                0, summary["strict_false_semantic_true_audit_count"]
            )
            task_dirs = [
                path
                for path in run_root.iterdir()
                if path.is_dir()
            ]
            self.assertEqual(21, len(task_dirs))
            for task_dir in task_dirs:
                present = {
                    path.name for path in task_dir.iterdir() if path.is_file()
                }
                self.assertTrue(
                    verifier.TASK_REQUIRED_ARTIFACTS <= present,
                    task_dir.name,
                )
                self.assertEqual(
                    b"", (task_dir / "codex_events.jsonl").read_bytes()
                )


if __name__ == "__main__":
    unittest.main()
