#!/usr/bin/env python3
"""Fixture-based artifact contract tests for the WorkBuddy C-group adapter."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

# Make the adapter package importable regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import run_condition as rc  # noqa: E402


ROOT = rc.repository_root()
RUNNER_PATH = ROOT / "experiments" / "skillnet_workbuddy" / "run_condition.py"
E1_TASK_IDS = [
    "GT01_SINGLE", "GT04_TECH_GOAL", "GT13_CROSS_INTERNAL_DEV_STAFF_DATA",
    "GT15_CROSS_SUPPLIER_CONTRACT_PO", "GT16_SPECIAL_SUPPLIER_FAIL",
]
# Runner creates these; the frozen verifier adds evaluation_trace/graph_overlay/result_row.
RUNNER_ARTIFACTS = {
    "run_metadata.json", "packet_manifest.json", "catalogue_snapshot.json",
    "codex_events.jsonl", "raw_response.txt", "schema_validation.json",
}


def load_gold_perfect_predictions() -> dict[str, dict[str, object]]:
    fixture = (
        ROOT / "SkillNet_Gold_Tasks_V4" / "evaluation"
        / "fixtures" / "gold_perfect_predictions.jsonl"
    )
    records: dict[str, dict[str, object]] = {}
    for line in fixture.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec["task_id"] in E1_TASK_IDS:
            records[rec["task_id"]] = rec
    return records


def write_fixture_responses(fixture_dir: Path, *, invalid_task_id: str | None = None) -> None:
    fixture_dir.mkdir()
    records = load_gold_perfect_predictions()
    for tid in E1_TASK_IDS:
        response = (
            "not-json\n"
            if tid == invalid_task_id
            else json.dumps(records[tid], ensure_ascii=False) + "\n"
        )
        (fixture_dir / f"{tid}.txt").write_text(response, encoding="utf-8")


def run_fixture_condition(
    tmp: Path, *, configuration: str = "C", run_id: str = "wb_contract_test",
    invalid_task_id: str | None = None,
) -> Path:
    fixture_dir = tmp / "fixtures"
    write_fixture_responses(fixture_dir, invalid_task_id=invalid_task_id)
    state_root = tmp / "state"
    argv = [
        str(RUNNER_PATH),
        "--experiment", "E1",
        "--configuration", configuration,
        "--size", "10",
        "--run-id", run_id,
        "--fixture-response-dir", str(fixture_dir),
        "--state-root", str(state_root),
    ]
    with patch.object(sys, "argv", argv):
        exit_code = rc.main()
        if exit_code != 0:
            raise AssertionError(f"fixture runner failed (exit {exit_code})")
    return state_root / "runs" / "E1" / configuration / "size_10" / run_id


class WorkBuddyAdapterTests(unittest.TestCase):
    def test_c_only_configuration(self) -> None:
        """A/B configurations are rejected."""
        with self.assertRaises((ValueError, SystemExit)):
            rc.resolve_condition(ROOT, "E0", "A", 46)
        with self.assertRaises((ValueError, SystemExit)):
            rc.resolve_condition(ROOT, "E0", "B", 46)

    def test_only_four_conditions_allowed(self) -> None:
        """Disallowed experiment/size combos are rejected."""
        with self.assertRaises((ValueError, SystemExit)):
            rc.resolve_condition(ROOT, "E1", "C", 20)
        with self.assertRaises((ValueError, SystemExit)):
            rc.resolve_condition(ROOT, "E0", "C", 10)

    def test_fixture_creates_complete_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = run_fixture_condition(Path(tmp))
            for tid in E1_TASK_IDS:
                task_dir = run_root / tid
                actual = {p.name for p in task_dir.iterdir() if p.is_file()}
                expected = RUNNER_ARTIFACTS | {"prediction.json"}
                self.assertTrue(
                    expected <= actual,
                    f"{tid}: missing {sorted(expected - actual)}",
                )
                meta = json.loads(
                    (task_dir / "run_metadata.json").read_text(encoding="utf-8")
                )
                for field in ("experiment_id", "task_id", "configuration",
                              "catalogue_size", "run_id", "start_time",
                              "end_time", "exit_code"):
                    self.assertIn(field, meta)
                # Verifier-only artifacts must NOT be created by the runner.
                self.assertFalse((task_dir / "evaluation_trace.json").exists())
                self.assertFalse((task_dir / "result_row.json").exists())

    def test_invalid_prediction_still_has_audit_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = run_fixture_condition(
                Path(tmp), invalid_task_id="GT16_SPECIAL_SUPPLIER_FAIL",
            )
            task_dir = run_root / "GT16_SPECIAL_SUPPLIER_FAIL"
            self.assertFalse((task_dir / "prediction.json").exists())
            for art in RUNNER_ARTIFACTS:
                self.assertTrue((task_dir / art).is_file(), art)

    def test_e1_size46_rejects_execute_without_derive(self) -> None:
        """E1-C-size46 must use --derive-e1-size46, never --execute."""
        argv = [
            str(RUNNER_PATH), "--experiment", "E1", "--configuration", "C",
            "--size", "46", "--run-id", "wb_guard_test", "--execute",
            "--model-id", "x", "--model-slug", "x",
        ]
        with patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit):
                rc.main()

    def test_derive_e1_size46_requires_e0_run(self) -> None:
        """Derivation without an existing E0-C-size46 run must fail."""
        with tempfile.TemporaryDirectory() as tmp:
            argv = [
                str(RUNNER_PATH), "--experiment", "E1", "--configuration", "C",
                "--size", "46", "--run-id", "wb_derive_guard",
                "--derive-e1-size46", "--model-slug", "x",
                "--state-root", str(Path(tmp) / "state"),
            ]
            with patch.object(sys, "argv", argv):
                with self.assertRaises(SystemExit):
                    rc.main()


class CliInvocationTests(unittest.TestCase):
    """Windows Node-script invocation prefix logic (no real CLI calls)."""

    def test_extensionless_script_prefixed_with_node_on_windows(self) -> None:
        fake_cli = Path("D:/wb/cli/bin/codebuddy")
        fake_node = Path("C:/node/node.exe")
        with patch.object(rc.os, "name", "nt"), patch.object(
            rc, "resolve_node", return_value=fake_node
        ):
            argv = rc.cli_invocation(fake_cli)
        self.assertEqual(argv, [str(fake_node), str(fake_cli)])

    def test_real_exe_runs_directly_on_windows(self) -> None:
        fake_cli = Path("C:/cb/codebuddy.exe")
        with patch.object(rc.os, "name", "nt"):
            argv = rc.cli_invocation(fake_cli)
        self.assertEqual(argv, [str(fake_cli)])

    def test_missing_node_raises_not_formal_ready_on_windows(self) -> None:
        fake_cli = Path("/opt/codebuddy")
        with patch.object(rc.os, "name", "nt"), patch.object(
            rc, "resolve_node", return_value=None
        ):
            with self.assertRaises(RuntimeError) as ctx:
                rc.cli_invocation(fake_cli)
        self.assertIn("WORKBUDDY_TRANSPORT_NOT_FORMAL_READY", str(ctx.exception))

    def test_posix_runs_script_directly(self) -> None:
        fake_cli = Path("/opt/codebuddy")
        with patch.object(rc.os, "name", "posix"):
            argv = rc.cli_invocation(fake_cli)
        self.assertEqual(argv, [str(fake_cli)])


if __name__ == "__main__":
    unittest.main()
