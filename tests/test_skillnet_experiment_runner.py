#!/usr/bin/env python3
"""Regression tests for the frozen SkillNet E0/E1 experiment runner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_E1_TASK_IDS = (
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
)
RUNNER_PATH = ROOT / "experiments" / "skillnet" / "run_condition.py"
SPEC = importlib.util.spec_from_file_location("skillnet_run_condition", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
sys.modules["run_condition"] = runner

VERIFY_PATH = ROOT / "experiments" / "skillnet" / "verify_condition.py"
VERIFY_SPEC = importlib.util.spec_from_file_location(
    "skillnet_verify_condition", VERIFY_PATH
)
assert VERIFY_SPEC and VERIFY_SPEC.loader
verifier = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(verifier)


class SkillNetExperimentRunnerTests(unittest.TestCase):
    def test_e1_inventory_is_all_21_tasks_for_every_condition(self) -> None:
        manifest = json.loads(
            (ROOT / "skillnet_run_guide_v1_1" / "E1_scale_manifest.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["task_ids"], list(EXPECTED_E1_TASK_IDS))
        for size in (10, 30, 46):
            for configuration in ("A", "B", "C"):
                _, _, task_ids = runner.resolve_condition(
                    ROOT, "E1", configuration, size
                )
                self.assertEqual(task_ids, list(EXPECTED_E1_TASK_IDS))

    def test_frozen_e1_gold_contains_all_canonical_task_records(self) -> None:
        full = json.loads(
            (ROOT / "SkillNet_Gold_Tasks_V4" / "02_Gold_Standard_21_V4.json")
            .read_text(encoding="utf-8")
        )
        frozen = json.loads(
            (
                ROOT
                / "experiments"
                / "skillnet"
                / "frozen_eval"
                / "E1_Gold_21_tasks.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(frozen["task_count"], 21)
        self.assertEqual(frozen["tasks"], full["tasks"])
        self.assertEqual(
            frozen["subset_provenance"]["task_ids"],
            list(EXPECTED_E1_TASK_IDS),
        )

    def test_live_runner_refuses_e1_size_46(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            argv = [
                str(RUNNER_PATH),
                "--experiment",
                "E1",
                "--configuration",
                "A",
                "--size",
                "46",
                "--run-id",
                "must_reuse_e0",
                "--fixture-response-dir",
                "/nonexistent-fixtures",
                "--state-root",
                temporary,
            ]
            with patch.object(sys, "argv", argv):
                with self.assertRaisesRegex(SystemExit, "E1 size 46 reuses E0"):
                    runner.main()

    def test_child_prompt_contains_complete_fixed_output_contract(self) -> None:
        catalogue = {
            "configuration": "A",
            "catalogue_size": 1,
            "skills": [
                {
                    "skill_id": "synthetic-current-skill",
                    "name": "Synthetic current skill",
                }
            ],
        }

        prompt = runner.build_child_prompt(
            "GT99_SYNTHETIC",
            "这是不属于 Gold 的合成任务。",
            catalogue,
        )

        for field in (
            "task_id",
            "use_skills",
            "selected_departments",
            "skill_sequence",
            "final_status",
            "blocked_by",
            "route_choice",
            "reason",
        ):
            self.assertIn(field, prompt)
        self.assertIn("completed", prompt)
        self.assertIn("blocked", prompt)
        self.assertIn("no_tool", prompt)
        self.assertIn("synthetic-current-skill", prompt)
        self.assertNotIn("finance-accounting", prompt)

    def test_codex_command_avoids_unsupported_transport_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            packet_dir = Path(temporary)
            raw_path = packet_dir / "raw_response.txt"
            completed = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            with patch.object(runner.subprocess, "run", return_value=completed):
                _, _, _, _, command = runner.execute_codex(
                    Path("/synthetic/codex"),
                    "synthetic prompt",
                    raw_path,
                    packet_dir,
                )

            self.assertNotIn("--output-schema", command)
            self.assertFalse((packet_dir / "output_schema.json").exists())
            self.assertIn("--ephemeral", command)
            self.assertEqual(command[-1], "-")

    def test_fixture_run_records_runtime_and_attempt_policy(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "skillnet_run_guide_v1_1"
                / "E1_scale_manifest.json"
            ).read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            fixture_dir = temporary_path / "fixtures"
            fixture_dir.mkdir()
            for task_id in manifest["task_ids"]:
                (fixture_dir / f"{task_id}.txt").write_text("{}\n", encoding="utf-8")

            state_root = temporary_path / "state"
            argv = [
                str(RUNNER_PATH),
                "--experiment",
                "E1",
                "--configuration",
                "A",
                "--size",
                "10",
                "--run-id",
                "setup_policy_test",
                "--fixture-response-dir",
                str(fixture_dir),
                "--state-root",
                str(state_root),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(runner.main(), 0)

            metadata_path = (
                state_root
                / "runs"
                / "E1"
                / "A"
                / "size_10"
                / "setup_policy_test"
                / "condition_metadata.json"
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["attempts_per_task"], 1)
            self.assertEqual(metadata["automatic_retries"], 0)
            self.assertTrue(metadata["transport_reconnects_allowed"])
            self.assertEqual(
                metadata["task_attempt_definition"],
                "one fresh codex exec process",
            )
            self.assertEqual(metadata["python"]["executable"], sys.executable)
            self.assertEqual(metadata["python"]["jsonschema_version"], "4.25.1")

    def test_verify_command_replays_the_current_python_executable(self) -> None:
        args = SimpleNamespace(
            experiment="E1",
            configuration="A",
            size=10,
            run_id="synthetic_verify_command",
            state_root=ROOT / "experiments" / "skillnet",
        )

        command = verifier.expected_verify_command(args)

        self.assertEqual(
            shlex.split(command)[0],
            sys.executable,
        )


if __name__ == "__main__":
    unittest.main()
