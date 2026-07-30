#!/usr/bin/env python3
"""Verify and evaluate one immutable SkillNet E1-v2 condition."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import evaluate_e1v2 as evaluator
import run_condition as runner


TASK_REQUIRED_ARTIFACTS = {
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


def mechanical_extract_final_object(
    raw: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    stripped = raw.strip()
    report = {
        "method": None,
        "candidate_count": 0,
        "selected_start": None,
        "selected_end": None,
        "errors": [],
    }
    if not stripped:
        report["errors"].append("empty_response")
        return None, report
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            report.update(
                {
                    "method": "whole_response_json",
                    "candidate_count": 1,
                    "selected_start": 0,
                    "selected_end": len(stripped),
                }
            )
            return value, report
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    candidates = []
    for start, character in enumerate(raw):
        if character != "{":
            continue
        try:
            value, length = decoder.raw_decode(raw[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            candidates.append((start, start + length, value))
    report["candidate_count"] = len(candidates)
    if not candidates:
        report["errors"].append("invalid_json_no_object")
        return None, report
    selected = sorted(candidates, key=lambda item: (item[1], -item[0]))[-1]
    report.update(
        {
            "method": "last_parseable_json_object",
            "selected_start": selected[0],
            "selected_end": selected[1],
        }
    )
    return selected[2], report


def result_root(
    state_root: Path,
    configuration: str,
    size: int,
    run_id: str,
) -> Path:
    return (
        state_root
        / "results"
        / runner.EXPERIMENT_ID
        / configuration
        / f"size_{size}"
        / run_id
    )


def build_trace(
    task: dict[str, Any],
    prediction: dict[str, Any] | None,
    row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "E1V2-1.0",
        "experiment_id": runner.EXPERIMENT_ID,
        "task_id": task["task_id"],
        "prediction_available": prediction is not None,
        "predicted_sequence": (
            prediction.get("skill_sequence", []) if prediction else []
        ),
        "skill_checks": {
            "required": task.get("required_skills", []),
            "optional": task.get("optional_skills", []),
            "missing": row["missing_required_skills"],
            "extra": row["extra_skills"],
            "forbidden_hits": row["forbidden_hits"],
            "repeated_completed": row["repeated_initial_skills"],
        },
        "department_checks": {
            "required": task.get("required_departments", []),
            "missing": row["missing_departments"],
            "extra": row["extra_departments"],
            "unknown": row["unknown_departments"],
        },
        "order_checks": {
            "results": row.get("hard_order_results", []),
            "violations": row["unsatisfied_order_pairs"],
        },
        "constraint_checks": {
            "conflict_violations": row["conflict_violations"],
            "strict_mutex_violations": row["strict_mutex_violations"],
            "semantic_mutex_violations": row["semantic_mutex_violations"],
            "strict_gold_constraint_violated": row[
                "strict_gold_constraint_violated"
            ],
            "semantic_gold_constraint_violated": row[
                "semantic_gold_constraint_violated"
            ],
        },
        "control_checks": {
            "final_status_correct": row["final_status_correct"],
            "blocked_reason_f1": row["blocked_reason_f1"],
            "blocked_flow_correct": row["blocked_flow_correct"],
            "no_tool_correct": row["no_tool_correct"],
            "strict_route_choice_correct": row[
                "strict_route_choice_correct"
            ],
            "semantic_route_choice_correct": row[
                "semantic_route_choice_correct"
            ],
            "semantic_route_judgment": row["semantic_route_judgment"],
        },
        "success_metrics": {
            "strict_functional_success": row[
                "strict_functional_success"
            ],
            "semantic_functional_success": row[
                "semantic_functional_success"
            ],
            "skill_routing_success": row["skill_routing_success"],
            "control_success": row["control_success"],
        },
        "severity_counts": {
            key: row[key]
            for key in (
                "missing_required_skill_count",
                "extra_skill_count",
                "forbidden_skill_count",
                "repeated_completed_skill_count",
                "unsatisfied_order_pair_count",
                "conflict_violation_count",
                "mutex_violation_count",
                "continue_after_block_count",
                "transport_failure_count",
            )
        },
    }


def normalize_edges(catalogue: dict[str, Any]) -> list[dict[str, Any]]:
    edges = []
    endpoints = {
        "prerequisite": ("before", "after"),
        "conflict": ("gate_skill", "blocked_skill"),
        "mutex": ("skill_a", "skill_b"),
        "enhances": ("source", "target"),
    }
    for relation_type, records in catalogue.get("relations", {}).items():
        left, right = endpoints[relation_type]
        for record in records:
            edges.append(
                {
                    "relation_type": relation_type,
                    "source": record[left],
                    "target": record[right],
                    "attributes": {
                        key: value
                        for key, value in record.items()
                        if key not in {left, right}
                    },
                }
            )
    return edges


def build_overlay(
    *,
    repo: Path,
    args: argparse.Namespace,
    task: dict[str, Any],
    prediction: dict[str, Any] | None,
    row: dict[str, Any],
) -> dict[str, Any]:
    c_path = runner.task_catalogue_path(
        repo, task["task_id"], args.size, "C"
    )
    c_catalogue = runner.load_json(c_path)
    cards = runner.load_json(c_path)["departments"]
    nodes = [
        {
            "skill_id": card["skill_id"],
            "department_id": card["department_id"],
        }
        for department in cards
        for card in department["skills"]
    ]
    sequence = prediction.get("skill_sequence", []) if prediction else []
    return {
        "schema_version": "E1V2-1.0",
        "post_evaluation_overlay": args.configuration in {"A", "B"},
        "overlay_read_phase": "after_response_and_evaluator",
        "overlay_catalogue_configuration": "C",
        "overlay_catalogue_path": str(c_path.relative_to(repo)),
        "overlay_catalogue_sha256": runner.sha256_file(c_path),
        "visible_nodes": nodes,
        "visible_edges": normalize_edges(c_catalogue),
        "selected_route": {
            "skill_sequence": sequence,
            "selected_departments": (
                prediction.get("selected_departments", [])
                if prediction
                else []
            ),
            "blocked_by": (
                prediction.get("blocked_by", []) if prediction else []
            ),
            "route_choice": (
                prediction.get("route_choice", {}) if prediction else {}
            ),
        },
        "violations": {
            "order": row["unsatisfied_order_pairs"],
            "conflict": row["conflict_violations"],
            "mutex": row["semantic_mutex_violations"],
        },
    }


def validate_process_evidence(
    condition_root: Path,
    condition_metadata: dict[str, Any],
    task_ids: list[str],
) -> dict[str, Any]:
    """Validate per-task process isolation without inventing missing evidence."""
    execution_mode = condition_metadata.get("execution_mode")
    errors: dict[str, list[str]] = {}
    thread_ids: list[str] = []
    temporary_cwds: list[str] = []
    child_pids: list[int] = []

    condition_errors = []
    if condition_metadata.get("attempts_per_task") != 1:
        condition_errors.append("attempts_per_task_must_equal_1")
    if condition_metadata.get("automatic_retries") != 0:
        condition_errors.append("automatic_retries_must_equal_0")
    if condition_metadata.get("resume_used") is not False:
        condition_errors.append("resume_used_must_be_false")
    if execution_mode == "codex":
        if condition_metadata.get("execution_order") != "serial":
            condition_errors.append("execution_order_must_be_serial")
        if condition_metadata.get("max_workers") != 1:
            condition_errors.append("max_workers_must_equal_1")
    elif execution_mode != "fixture":
        condition_errors.append("unknown_execution_mode")
    if condition_errors:
        errors["_condition"] = condition_errors

    required_fields = {
        "child_pid",
        "codex_thread_id",
        "thread_id_missing_reason",
        "temporary_cwd",
        "start_time",
        "end_time",
        "duration_seconds",
        "command_redacted",
        "exit_code",
        "attempt_number",
        "automatic_retry",
    }
    resume_tokens = {"--resume", "resume", "--continue", "continue", "-r"}
    for task_id in task_ids:
        task_errors = []
        task_dir = condition_root / task_id
        metadata_path = task_dir / "run_metadata.json"
        if not metadata_path.is_file():
            errors[task_id] = ["run_metadata_missing"]
            continue
        metadata = runner.load_json(metadata_path)
        missing_fields = sorted(required_fields - set(metadata))
        task_errors.extend(
            f"missing_process_evidence_field:{field}"
            for field in missing_fields
        )
        if metadata.get("attempt_number") != 1:
            task_errors.append("attempt_number_must_equal_1")
        if metadata.get("automatic_retry") is not False:
            task_errors.append("automatic_retry_must_be_false")
        if not isinstance(metadata.get("start_time"), str):
            task_errors.append("start_time_missing")
        if not isinstance(metadata.get("end_time"), str):
            task_errors.append("end_time_missing")
        duration = metadata.get("duration_seconds")
        if not isinstance(duration, (int, float)) or duration < 0:
            task_errors.append("duration_seconds_invalid")

        if execution_mode == "fixture":
            if metadata.get("execution_mode") != "fixture":
                task_errors.append("fixture_execution_mode_mismatch")
            if metadata.get("child_pid") is not None:
                task_errors.append("fixture_child_pid_must_be_null")
            if metadata.get("codex_thread_id") is not None:
                task_errors.append("fixture_thread_id_must_be_null")
            if metadata.get("temporary_cwd") is not None:
                task_errors.append("fixture_temporary_cwd_must_be_null")
            if (
                metadata.get("thread_id_missing_reason")
                != "fixture_mode_no_codex_process"
            ):
                task_errors.append("fixture_thread_missing_reason_invalid")
        elif execution_mode == "codex":
            child_pid = metadata.get("child_pid")
            if not isinstance(child_pid, int) or child_pid <= 0:
                task_errors.append("child_pid_invalid")
            else:
                child_pids.append(child_pid)
            temporary_cwd = metadata.get("temporary_cwd")
            if not isinstance(temporary_cwd, str) or not temporary_cwd:
                task_errors.append("temporary_cwd_invalid")
            else:
                temporary_cwds.append(temporary_cwd)

            command = metadata.get("command_redacted")
            if not isinstance(command, list) or not all(
                isinstance(item, str) for item in command
            ):
                task_errors.append("command_redacted_invalid")
            else:
                if "--ephemeral" not in command:
                    task_errors.append("ephemeral_flag_missing")
                if any(token in resume_tokens for token in command):
                    task_errors.append("resume_or_continue_forbidden")
                if command != metadata.get("command"):
                    task_errors.append("redacted_command_mismatch")

            events_path = task_dir / "codex_events.jsonl"
            event_thread_id = (
                runner.codex_thread_id_from_events(events_path.read_bytes())
                if events_path.is_file()
                else None
            )
            recorded_thread_id = metadata.get("codex_thread_id")
            if recorded_thread_id != event_thread_id:
                task_errors.append("thread_id_does_not_match_raw_events")
            if isinstance(recorded_thread_id, str) and recorded_thread_id:
                thread_ids.append(recorded_thread_id)
                if metadata.get("thread_id_missing_reason") is not None:
                    task_errors.append(
                        "thread_missing_reason_present_with_thread_id"
                    )
            else:
                if metadata.get("exit_code") == 0:
                    task_errors.append(
                        "successful_process_missing_thread_started"
                    )
                if (
                    metadata.get("thread_id_missing_reason")
                    != "codex_process_failed_before_thread_started"
                ):
                    task_errors.append("thread_missing_reason_invalid")
        if task_errors:
            errors[task_id] = task_errors

    duplicate_thread_ids = sorted(
        thread_id for thread_id in set(thread_ids)
        if thread_ids.count(thread_id) > 1
    )
    duplicate_temporary_cwds = sorted(
        temporary_cwd for temporary_cwd in set(temporary_cwds)
        if temporary_cwds.count(temporary_cwd) > 1
    )
    if duplicate_thread_ids:
        errors.setdefault("_condition", []).append(
            "duplicate_codex_thread_ids"
        )
    if duplicate_temporary_cwds:
        errors.setdefault("_condition", []).append(
            "duplicate_temporary_cwds"
        )
    return {
        "execution_mode": execution_mode,
        "task_count": len(task_ids),
        "child_pid_count": len(child_pids),
        "codex_thread_id_count": len(thread_ids),
        "temporary_cwd_count": len(temporary_cwds),
        "unique_codex_thread_id_count": len(set(thread_ids)),
        "unique_temporary_cwd_count": len(set(temporary_cwds)),
        "duplicate_codex_thread_ids": duplicate_thread_ids,
        "duplicate_temporary_cwds": duplicate_temporary_cwds,
        "errors": errors,
        "valid": not errors,
    }


def verify(args: argparse.Namespace) -> int:
    repo = runner.repository_root()
    state_root = args.state_root.resolve()
    gold, task_ids, tasks = runner.load_condition(
        repo, args.configuration, args.size
    )
    condition_root = runner.run_root(
        state_root, args.configuration, args.size, args.run_id
    )
    metadata_path = condition_root / "condition_metadata.json"
    if not metadata_path.is_file():
        raise RuntimeError(f"Missing condition: {condition_root}")
    metadata = runner.load_json(metadata_path)
    expected_identity = {
        "experiment_id": runner.EXPERIMENT_ID,
        "configuration": args.configuration,
        "size": args.size,
        "run_id": args.run_id,
        "task_ids": task_ids,
        "gold_sha256": runner.sha256_file(runner.gold_path(repo)),
        "pool_manifest_sha256": runner.sha256_file(
            runner.pool_manifest_path(repo)
        ),
    }
    for key, value in expected_identity.items():
        if metadata.get(key) != value:
            raise RuntimeError(f"Condition identity mismatch: {key}")
    validation_path = condition_root / "condition_validation.json"
    if validation_path.exists():
        raise RuntimeError(f"Verification already exists: {validation_path}")
    final_root = result_root(
        state_root, args.configuration, args.size, args.run_id
    )
    if final_root.exists():
        raise RuntimeError(f"Results already exist: {final_root}")
    final_root.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=".e1v2_verify_", dir=final_root.parent)
    )
    promoted = False
    try:
        predictions_dir = temporary_root / "predictions"
        records_dir = temporary_root / "verification_records"
        predictions_dir.mkdir()
        records_dir.mkdir()
        schema = runner.load_json(runner.schema_path(repo))
        rows = []
        evaluated: dict[str, dict[str, Any] | None] = {}
        for task_id in task_ids:
            task_dir = condition_root / task_id
            raw_path = task_dir / "raw_response.txt"
            raw = raw_path.read_text(encoding="utf-8") if raw_path.is_file() else ""
            prediction, extraction = mechanical_extract_final_object(raw)
            schema_errors = (
                runner.schema_errors(prediction, schema, task_id)
                if prediction is not None
                else [{"path": "", "message": item} for item in extraction["errors"]]
            )
            schema_valid = prediction is not None and not schema_errors
            run_metadata_path = task_dir / "run_metadata.json"
            run_metadata = (
                runner.load_json(run_metadata_path)
                if run_metadata_path.is_file()
                else {"exit_code": 4}
            )
            transport_failure = run_metadata.get("exit_code") != 0
            evaluator_prediction = (
                prediction
                if prediction is not None
                else {
                    "task_id": task_id,
                    "_parse_error": (
                        extraction["errors"][0]
                        if extraction["errors"]
                        else "missing_prediction"
                    ),
                }
            )
            row = evaluator.evaluate_record(
                evaluator_prediction,
                tasks[task_id],
                gold,
                args.configuration,
                args.run_id,
                transport_failure=transport_failure,
                schema_valid=schema_valid,
            )
            rows.append(row)
            evaluated[task_id] = prediction if schema_valid else None
            record = {
                "task_id": task_id,
                "raw_response_path": str(raw_path),
                "raw_response_sha256": (
                    runner.sha256_file(raw_path)
                    if raw_path.is_file()
                    else None
                ),
                "extraction": extraction,
                "schema_valid": schema_valid,
                "schema_errors": schema_errors,
                "transport_failure": transport_failure,
                "included_in_predictions_directory": schema_valid,
            }
            runner.write_json(records_dir / f"{task_id}.json", record)
            if schema_valid:
                runner.write_json(
                    predictions_dir / f"{task_id}.json", prediction
                )

        summary = evaluator.summarize_condition(rows)
        audits = [
            row["semantic_expression_audit"]
            for row in rows
            if row["semantic_expression_audit"] is not None
        ]
        runner.write_json(
            temporary_root / "per_task_results.json", rows
        )
        runner.write_json(
            temporary_root / "condition_summary.json", summary
        )
        runner.write_json(
            temporary_root / "semantic_expression_audit.json", audits
        )
        runner.write_json(
            temporary_root / "evaluation_provenance.json",
            {
                "schema_version": "E1V2-1.0",
                "experiment_id": runner.EXPERIMENT_ID,
                "gold_path": str(runner.gold_path(repo).relative_to(repo)),
                "gold_sha256": runner.sha256_file(runner.gold_path(repo)),
                "evaluator_path": str(
                    Path(evaluator.__file__).resolve().relative_to(repo)
                ),
                "evaluator_sha256": runner.sha256_file(
                    Path(evaluator.__file__).resolve()
                ),
                "semantic_normalization_sha256": evaluator.sha256_file(
                    evaluator.DEFAULT_NORMALIZATION
                ),
                "metric_definitions_sha256": evaluator.sha256_file(
                    Path(__file__).resolve().parent
                    / "metric_definitions.json"
                ),
            },
        )
        os.rename(temporary_root, final_root)
        promoted = True

        rows_by_id = {row["task_id"]: row for row in rows}
        for task_id in task_ids:
            task_dir = condition_root / task_id
            prediction = evaluated[task_id]
            row = rows_by_id[task_id]
            runner.write_json(
                task_dir / "evaluation_trace.json",
                build_trace(tasks[task_id], prediction, row),
            )
            runner.write_json(
                task_dir / "graph_overlay.json",
                build_overlay(
                    repo=repo,
                    args=args,
                    task=tasks[task_id],
                    prediction=prediction,
                    row=row,
                ),
            )
            runner.write_json(task_dir / "result_row.json", row)

        missing = {}
        for task_id in task_ids:
            present = {
                path.name
                for path in (condition_root / task_id).iterdir()
                if path.is_file()
            }
            task_missing = sorted(TASK_REQUIRED_ARTIFACTS - present)
            if task_missing:
                missing[task_id] = task_missing
        process_evidence = validate_process_evidence(
            condition_root,
            metadata,
            task_ids,
        )
        status = (
            "complete"
            if not missing
            and process_evidence["valid"]
            and summary["consistency_counts"][
                "semantic_true_skill_routing_false"
            ]
            == 0
            else "incomplete"
        )
        runner.write_json(
            validation_path,
            {
                "schema_version": "E1V2-1.0",
                "experiment_id": runner.EXPERIMENT_ID,
                "status": status,
                "configuration": args.configuration,
                "catalogue_size": args.size,
                "run_id": args.run_id,
                "task_count": len(task_ids),
                "missing_artifacts": missing,
                "process_evidence": process_evidence,
                "semantic_true_skill_routing_false": summary[
                    "consistency_counts"
                ]["semantic_true_skill_routing_false"],
                "result_root": str(final_root),
            },
        )
    except Exception:
        if not promoted:
            shutil.rmtree(temporary_root, ignore_errors=True)
        raise
    print(
        json.dumps(
            {
                "status": status,
                "result_root": str(final_root),
                "task_count": len(task_ids),
                "consistency_counts": summary["consistency_counts"],
                "process_evidence": process_evidence,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if status == "complete" else 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", choices=("A", "B", "C"), required=True)
    parser.add_argument("--size", type=int, choices=(10, 30, 46), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--state-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not runner.RUN_ID_PATTERN.fullmatch(args.run_id):
        raise SystemExit("Invalid run_id")
    return verify(args)


if __name__ == "__main__":
    raise SystemExit(main())
