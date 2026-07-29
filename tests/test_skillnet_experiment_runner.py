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
