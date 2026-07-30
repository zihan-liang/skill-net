#!/usr/bin/env python3
"""Fixture-only runner/verifier contract for SkillNet E1-v2."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


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
            self.assertEqual(
                0,
                summary["consistency_counts"][
                    "skill_routing_true_control_false"
                ],
            )
            self.assertTrue(condition["process_evidence"]["valid"])
            self.assertEqual(
                0, condition["process_evidence"]["child_pid_count"]
            )
            self.assertEqual(
                0, condition["process_evidence"]["codex_thread_id_count"]
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
                metadata = json.loads(
                    (task_dir / "run_metadata.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual("fixture", metadata["execution_mode"])
                self.assertIsNone(metadata["child_pid"])
                self.assertIsNone(metadata["codex_thread_id"])
                self.assertIsNone(metadata["temporary_cwd"])
                self.assertEqual(
                    "fixture_mode_no_codex_process",
                    metadata["thread_id_missing_reason"],
                )

    def test_execute_codex_uses_one_popen_and_extracts_own_thread_id(
        self,
    ) -> None:
        events = (
            b'{"type":"thread.started","thread_id":"thread-one"}\n'
            b'{"type":"turn.completed"}\n'
        )
        process = MagicMock()
        process.pid = 4242
        process.returncode = 0
        process.communicate.return_value = (events, b"")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            events_path = root / "codex_events.jsonl"
            with patch.object(
                runner.subprocess,
                "Popen",
                return_value=process,
            ) as popen:
                result = runner.execute_codex(
                    "synthetic prompt",
                    root / "raw_response.txt",
                    events_path,
                    root,
                )
        self.assertEqual(1, popen.call_count)
        process.communicate.assert_called_once_with(
            input=b"synthetic prompt"
        )
        self.assertEqual(0, result[0])
        self.assertEqual(4242, result[3])
        self.assertEqual("thread-one", result[4])
        self.assertIsNone(result[5])

    def test_verifier_rejects_duplicate_formal_thread_and_cwd(
        self,
    ) -> None:
        condition_metadata = {
            "execution_mode": "codex",
            "execution_order": "serial",
            "max_workers": 1,
            "attempts_per_task": 1,
            "automatic_retries": 0,
            "resume_used": False,
        }
        with tempfile.TemporaryDirectory() as temporary:
            condition_root = Path(temporary)
            for task_id, child_pid in (("T1", 101), ("T2", 102)):
                task_dir = condition_root / task_id
                task_dir.mkdir()
                (task_dir / "codex_events.jsonl").write_text(
                    '{"type":"thread.started","thread_id":"duplicate"}\n',
                    encoding="utf-8",
                )
                (task_dir / "run_metadata.json").write_text(
                    json.dumps(
                        {
                            "execution_mode": "codex",
                            "attempt_number": 1,
                            "automatic_retry": False,
                            "child_pid": child_pid,
                            "codex_thread_id": "duplicate",
                            "thread_id_missing_reason": None,
                            "temporary_cwd": "/tmp/duplicate",
                            "start_time": "2026-07-30T00:00:00+00:00",
                            "end_time": "2026-07-30T00:00:01+00:00",
                            "duration_seconds": 1.0,
                            "exit_code": 0,
                            "command": ["codex", "exec", "--ephemeral"],
                            "command_redacted": [
                                "codex",
                                "exec",
                                "--ephemeral",
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
            report = verifier.validate_process_evidence(
                condition_root,
                condition_metadata,
                ["T1", "T2"],
            )
        self.assertFalse(report["valid"])
        self.assertEqual(["duplicate"], report["duplicate_codex_thread_ids"])
        self.assertEqual(
            ["/tmp/duplicate"],
            report["duplicate_temporary_cwds"],
        )

    def test_verifier_accepts_real_failure_before_thread_started(
        self,
    ) -> None:
        condition_metadata = {
            "execution_mode": "codex",
            "execution_order": "serial",
            "max_workers": 1,
            "attempts_per_task": 1,
            "automatic_retries": 0,
            "resume_used": False,
        }
        with tempfile.TemporaryDirectory() as temporary:
            condition_root = Path(temporary)
            task_dir = condition_root / "T1"
            task_dir.mkdir()
            (task_dir / "codex_events.jsonl").write_bytes(b"")
            (task_dir / "run_metadata.json").write_text(
                json.dumps(
                    {
                        "execution_mode": "codex",
                        "attempt_number": 1,
                        "automatic_retry": False,
                        "child_pid": 103,
                        "codex_thread_id": None,
                        "thread_id_missing_reason": (
                            "codex_process_failed_before_thread_started"
                        ),
                        "temporary_cwd": "/tmp/unique-task-cwd",
                        "start_time": "2026-07-30T00:00:00+00:00",
                        "end_time": "2026-07-30T00:00:01+00:00",
                        "duration_seconds": 1.0,
                        "exit_code": 7,
                        "command": ["codex", "exec", "--ephemeral"],
                        "command_redacted": [
                            "codex",
                            "exec",
                            "--ephemeral",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = verifier.validate_process_evidence(
                condition_root,
                condition_metadata,
                ["T1"],
            )
        self.assertTrue(report["valid"])
        self.assertEqual(1, report["child_pid_count"])
        self.assertEqual(0, report["codex_thread_id_count"])


if __name__ == "__main__":
    unittest.main()
