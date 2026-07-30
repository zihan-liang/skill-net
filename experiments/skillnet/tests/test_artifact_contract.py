#!/usr/bin/env python3
"""Artifact-contract tests for the SkillNet condition runner and verifier."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
SKILLNET_DIR = ROOT / "experiments" / "skillnet"
RUNNER_PATH = SKILLNET_DIR / "run_condition.py"
VERIFY_PATH = SKILLNET_DIR / "verify_condition.py"

RUNNER_SPEC = importlib.util.spec_from_file_location(
    "skillnet_artifact_runner", RUNNER_PATH
)
assert RUNNER_SPEC and RUNNER_SPEC.loader
runner = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(runner)
sys.modules["run_condition"] = runner

VERIFY_SPEC = importlib.util.spec_from_file_location(
    "skillnet_artifact_verifier", VERIFY_PATH
)
assert VERIFY_SPEC and VERIFY_SPEC.loader
verifier = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(verifier)


E1_TASK_IDS = [
    "GT01_SINGLE",
    "GT04_TECH_GOAL",
    "GT13_CROSS_INTERNAL_DEV_STAFF_DATA",
    "GT15_CROSS_SUPPLIER_CONTRACT_PO",
    "GT16_SPECIAL_SUPPLIER_FAIL",
]
ALWAYS_REQUIRED_TASK_ARTIFACTS = {
    "run_metadata.json",
    "packet_manifest.json",
    "catalogue_snapshot.json",
    "codex_events.jsonl",
    "raw_response.txt",
    "schema_validation.json",
    "evaluation_trace.json",
    "graph_overlay.json",
    "result_row.json",
}


def load_gold_perfect_predictions() -> dict[str, dict[str, object]]:
    fixture_path = (
        ROOT
        / "SkillNet_Gold_Tasks_V4"
        / "evaluation"
        / "fixtures"
        / "gold_perfect_predictions.jsonl"
    )
    records = {}
    for line in fixture_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["task_id"] in E1_TASK_IDS:
            records[record["task_id"]] = record
    return records


def write_fixture_responses(
    fixture_dir: Path,
    *,
    invalid_task_id: str | None = None,
) -> None:
    fixture_dir.mkdir()
    records = load_gold_perfect_predictions()
    for task_id in E1_TASK_IDS:
        if task_id == invalid_task_id:
            response = "not-json\n"
        else:
            response = json.dumps(records[task_id], ensure_ascii=False) + "\n"
        (fixture_dir / f"{task_id}.txt").write_text(
            response, encoding="utf-8"
        )


def run_fixture_condition(
    temporary_path: Path,
    *,
    configuration: str = "A",
    run_id: str = "artifact_contract",
    invalid_task_id: str | None = None,
) -> tuple[Path, Path]:
    fixture_dir = temporary_path / "fixtures"
    write_fixture_responses(fixture_dir, invalid_task_id=invalid_task_id)
    state_root = temporary_path / "state"
    argv = [
        str(RUNNER_PATH),
        "--experiment",
        "E1",
        "--configuration",
        configuration,
        "--size",
        "10",
        "--run-id",
        run_id,
        "--fixture-response-dir",
        str(fixture_dir),
        "--state-root",
        str(state_root),
    ]
    with patch.object(sys, "argv", argv):
        if runner.main() != 0:
            raise AssertionError("fixture runner failed")
    run_root = (
        state_root
        / "runs"
        / "E1"
        / configuration
        / "size_10"
        / run_id
    )
    return state_root, run_root


def verify_fixture_condition(
    state_root: Path,
    *,
    configuration: str = "A",
    run_id: str = "artifact_contract",
) -> int:
    argv = [
        str(VERIFY_PATH),
        "--experiment",
        "E1",
        "--configuration",
        configuration,
        "--size",
        "10",
        "--run-id",
        run_id,
        "--state-root",
        str(state_root),
    ]
    with patch.object(sys, "argv", argv):
        return verifier.main()


class SkillNetArtifactContractTests(unittest.TestCase):
    def test_new_conversation_entrypoint_names_existing_prompt_files(self) -> None:
        standard_run_prompt = (
            ROOT / "SkillNet_Standard_RUN_Commands_E0_E1_v3_CN.txt"
        )
        text = standard_run_prompt.read_text(encoding="utf-8")
        authoritative_files = (
            "SkillNet_Codex_Setup_Prompt_E0_E1_v3_CN(1).txt",
            "SkillNet_Standard_RUN_Commands_E0_E1_v3_CN.txt",
            "experiments/skillnet/RUNBOOK.md",
        )

        for relative_path in authoritative_files:
            self.assertIn(relative_path, text)
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

        self.assertNotIn("experiments/skillnet/prompts/", text)

    def test_codex_json_events_are_saved_byte_for_byte(self) -> None:
        events = (
            b'{"type":"thread.started","thread_id":"synthetic"}\n'
            b'{"type":"turn.completed","usage":{}}\n'
        )
        with tempfile.TemporaryDirectory() as temporary:
            packet_dir = Path(temporary)
            raw_path = packet_dir / "raw_response.txt"
            events_path = packet_dir / "codex_events.jsonl"

            def fake_run(command: list[str], **_kwargs: object) -> object:
                raw_path.write_text('{"task_id":"SYNTHETIC"}\n', encoding="utf-8")
                return subprocess.CompletedProcess(
                    args=command,
                    returncode=0,
                    stdout=events,
                    stderr=b"synthetic stderr\n",
                )

            with patch.object(runner.subprocess, "run", side_effect=fake_run):
                _, _, _, _, command = runner.execute_codex(
                    Path("/synthetic/codex"),
                    "synthetic prompt",
                    raw_path,
                    packet_dir,
                    events_path=events_path,
                )

            self.assertIn("--json", command)
            self.assertIn("--output-last-message", command)
            self.assertEqual(events_path.read_bytes(), events)

    def test_fixture_verification_creates_complete_task_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_root, run_root = run_fixture_condition(Path(temporary))
            self.assertEqual(verify_fixture_condition(state_root), 0)

            for task_id in E1_TASK_IDS:
                task_dir = run_root / task_id
                actual = {path.name for path in task_dir.iterdir() if path.is_file()}
                self.assertTrue(
                    ALWAYS_REQUIRED_TASK_ARTIFACTS <= actual,
                    f"{task_id}: {sorted(ALWAYS_REQUIRED_TASK_ARTIFACTS - actual)}",
                )
                self.assertIn("prediction.json", actual)
                self.assertEqual(
                    (task_dir / "codex_events.jsonl").read_bytes(), b""
                )
                snapshot = json.loads(
                    (task_dir / "catalogue_snapshot.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(snapshot["configuration"], "A")
                self.assertNotIn("relations", snapshot)

                metadata = json.loads(
                    (task_dir / "run_metadata.json").read_text(encoding="utf-8")
                )
                for field in (
                    "experiment_id",
                    "task_id",
                    "configuration",
                    "catalogue_size",
                    "run_id",
                    "runtime_repo_commit",
                    "catalogue_source_commit",
                    "codex_cli_version",
                    "model",
                    "start_time",
                    "end_time",
                    "duration_seconds",
                    "exit_code",
                    "input_hashes",
                    "command",
                    "stderr",
                ):
                    self.assertIn(field, metadata)

                trace = json.loads(
                    (task_dir / "evaluation_trace.json").read_text(
                        encoding="utf-8"
                    )
                )
                for field in (
                    "predicted_sequence",
                    "skill_checks",
                    "department_checks",
                    "hard_order_checks",
                    "forbidden_checks",
                    "conflict_checks",
                    "mutex_checks",
                    "final_status_check",
                    "route_choice_check",
                    "blocked_checks",
                    "failure_tags",
                ):
                    self.assertIn(field, trace)

                overlay = json.loads(
                    (task_dir / "graph_overlay.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertTrue(overlay["post_evaluation_overlay"])
                self.assertEqual(overlay["overlay_catalogue_configuration"], "C")
                self.assertGreater(len(overlay["visible_nodes"]), 0)
                self.assertGreater(len(overlay["visible_edges"]), 0)
                for field in (
                    "selected_route",
                    "sequence_positions",
                    "gold_nodes",
                    "violated_edges",
                    "relation_types",
                    "metadata",
                ):
                    self.assertIn(field, overlay)
                if task_id == "GT16_SPECIAL_SUPPLIER_FAIL":
                    self.assertEqual(
                        set(overlay["gold_nodes"]["blocked"]),
                        {
                            "procurement-supplier-selection",
                            "procurement-contract-generation",
                        },
                    )
                    self.assertEqual(
                        overlay["gold_nodes"]["blockers"],
                        ["procurement-supplier-qualification"],
                    )

                result_row = json.loads(
                    (task_dir / "result_row.json").read_text(encoding="utf-8")
                )
                self.assertEqual(result_row["task_id"], task_id)

            condition = json.loads(
                (run_root / "condition_validation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(condition["status"], "complete")
            self.assertEqual(condition["missing_artifacts"], {})

    def test_b_overlay_reads_c_only_as_post_evaluation_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_root, run_root = run_fixture_condition(
                Path(temporary),
                configuration="B",
                run_id="b_post_evaluation_overlay",
            )
            self.assertEqual(
                verify_fixture_condition(
                    state_root,
                    configuration="B",
                    run_id="b_post_evaluation_overlay",
                ),
                0,
            )
            task_dir = run_root / E1_TASK_IDS[0]
            snapshot = json.loads(
                (task_dir / "catalogue_snapshot.json").read_text(
                    encoding="utf-8"
                )
            )
            overlay = json.loads(
                (task_dir / "graph_overlay.json").read_text(encoding="utf-8")
            )
            self.assertEqual(snapshot["configuration"], "B")
            self.assertNotIn("relations", snapshot)
            self.assertTrue(overlay["post_evaluation_overlay"])
            self.assertTrue(overlay["relations_loaded_after_response"])
            self.assertEqual(
                overlay["metadata"]["overlay_read_phase"],
                "after_response_and_evaluator",
            )

    def test_invalid_prediction_is_absent_but_audit_artifacts_are_complete(self) -> None:
        invalid_task_id = "GT16_SPECIAL_SUPPLIER_FAIL"
        with tempfile.TemporaryDirectory() as temporary:
            state_root, run_root = run_fixture_condition(
                Path(temporary),
                run_id="invalid_prediction",
                invalid_task_id=invalid_task_id,
            )
            self.assertEqual(
                verify_fixture_condition(
                    state_root, run_id="invalid_prediction"
                ),
                0,
            )

            task_dir = run_root / invalid_task_id
            self.assertFalse((task_dir / "prediction.json").exists())
            for filename in ALWAYS_REQUIRED_TASK_ARTIFACTS:
                self.assertTrue((task_dir / filename).is_file(), filename)
            validation = json.loads(
                (task_dir / "schema_validation.json").read_text(encoding="utf-8")
            )
            self.assertFalse(validation["schema_valid"])
            result_row = json.loads(
                (task_dir / "result_row.json").read_text(encoding="utf-8")
            )
            self.assertFalse(result_row["format_valid"])

    def test_missing_required_artifact_marks_condition_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_root, run_root = run_fixture_condition(
                Path(temporary), run_id="missing_artifact"
            )
            missing_path = run_root / E1_TASK_IDS[0] / "packet_manifest.json"
            if missing_path.exists():
                missing_path.unlink()

            self.assertNotEqual(
                verify_fixture_condition(
                    state_root, run_id="missing_artifact"
                ),
                0,
            )
            condition = json.loads(
                (run_root / "condition_validation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(condition["status"], "incomplete")
            self.assertIn(E1_TASK_IDS[0], condition["missing_artifacts"])
            self.assertIn(
                "packet_manifest.json",
                condition["missing_artifacts"][E1_TASK_IDS[0]],
            )


if __name__ == "__main__":
    unittest.main()
