#!/usr/bin/env python3
"""Verify and deterministically evaluate one SkillNet condition run."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import run_condition as runner


E1_GOLD_FILENAME = "E1_Gold_21_tasks.json"
E1_VALIDATION_FILENAME = "E1_Gold_21_tasks_validation.json"
VERIFIER_REQUIRED_ARTIFACTS = (
    "evaluation_trace.json",
    "graph_overlay.json",
    "result_row.json",
)


def evaluator_path(repo: Path) -> Path:
    return (
        repo
        / "SkillNet_Gold_Tasks_V4"
        / "evaluation"
        / "evaluate_skillnet.py"
    )


def full_gold_path(repo: Path) -> Path:
    return repo / "SkillNet_Gold_Tasks_V4" / "02_Gold_Standard_21_V4.json"


def manifest_path(repo: Path) -> Path:
    return repo / "skillnet_run_guide_v1_1" / "E1_scale_manifest.json"


def frozen_eval_dir() -> Path:
    return Path(__file__).resolve().parent / "frozen_eval"


def frozen_e1_gold_path() -> Path:
    return frozen_eval_dir() / E1_GOLD_FILENAME


def expected_e1_gold(repo: Path) -> dict[str, Any]:
    source_path = full_gold_path(repo)
    e1_manifest_path = manifest_path(repo)
    source = runner.load_json(source_path)
    manifest = runner.load_json(e1_manifest_path)
    task_ids = manifest.get("task_ids", [])

    source_tasks = source.get("tasks", [])
    by_id = {task.get("task_id"): task for task in source_tasks}
    if len(by_id) != len(source_tasks):
        raise ValueError("Full Gold contains duplicate task IDs")
    canonical_task_ids = sorted(by_id, key=lambda item: int(item[2:4]))
    if task_ids != canonical_task_ids:
        raise ValueError(
            "E1 manifest task IDs must exactly equal the ordered canonical "
            "GT01-GT21 Gold inventory"
        )

    gold = copy.deepcopy(source)
    gold["task_count"] = len(task_ids)
    gold["tasks"] = [copy.deepcopy(by_id[task_id]) for task_id in task_ids]
    gold["subset_provenance"] = {
        "source_gold_path": str(source_path.relative_to(repo)),
        "source_gold_sha256": runner.sha256_file(source_path),
        "source_gold_task_count": len(source_tasks),
        "manifest_path": str(e1_manifest_path.relative_to(repo)),
        "manifest_sha256": runner.sha256_file(e1_manifest_path),
        "task_ids": task_ids,
        "task_records_copied_without_modification": True,
    }
    return gold


def stable_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def install_if_absent_or_identical(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise RuntimeError(
                f"Refusing to overwrite non-identical frozen file: {path}"
            )
        return
    with path.open("xb") as handle:
        handle.write(content)


def run_gold_validation(
    repo: Path,
    gold_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="skillnet_gold_validation_") as temp:
        temporary_output = Path(temp) / "validation.json"
        command = [
            sys.executable,
            str(evaluator_path(repo)),
            "validate-package",
            "--gold",
            str(gold_path),
            "--output",
            str(temporary_output),
        ]
        process = subprocess.run(
            command,
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if not temporary_output.is_file():
            raise RuntimeError(
                "Evaluator did not create Gold validation output. "
                f"exit={process.returncode}, stderr={process.stderr}"
            )
        report = runner.load_json(temporary_output)
        if process.returncode != 0 or report.get("valid") is not True:
            raise RuntimeError(
                "21-task E1 Gold failed evaluator validation: "
                f"exit={process.returncode}, report={report}"
            )
        install_if_absent_or_identical(
            output_path, temporary_output.read_bytes()
        )
        return {
            "command": command,
            "exit_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "report": report,
        }


def prepare_frozen_e1_gold(repo: Path) -> dict[str, Any]:
    gold = expected_e1_gold(repo)
    output = frozen_e1_gold_path()
    install_if_absent_or_identical(output, stable_json_bytes(gold))

    source = runner.load_json(full_gold_path(repo))
    source_by_id = {task["task_id"]: task for task in source["tasks"]}
    for task in gold["tasks"]:
        if task != source_by_id[task["task_id"]]:
            raise RuntimeError(
                f"E1 task record changed during extraction: {task['task_id']}"
            )

    validation_path = frozen_eval_dir() / E1_VALIDATION_FILENAME
    validation = run_gold_validation(repo, output, validation_path)
    return {
        "gold_path": str(output),
        "gold_sha256": runner.sha256_file(output),
        "source_gold_sha256": gold["subset_provenance"][
            "source_gold_sha256"
        ],
        "manifest_sha256": gold["subset_provenance"]["manifest_sha256"],
        "task_ids": gold["subset_provenance"]["task_ids"],
        "validation_path": str(validation_path),
        "validation": validation["report"],
    }


def validate_frozen_e1_gold(repo: Path) -> dict[str, Any]:
    path = frozen_e1_gold_path()
    if not path.is_file():
        raise RuntimeError(
            f"Missing frozen 21-task E1 Gold; run --prepare-e1-gold: {path}"
        )
    actual = runner.load_json(path)
    expected = expected_e1_gold(repo)
    if actual != expected:
        raise RuntimeError(
            "Frozen 21-task E1 Gold no longer matches the current full Gold "
            "and E1 manifest"
        )
    return actual


def mechanical_extract_final_object(
    raw: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    stripped = raw.strip()
    report: dict[str, Any] = {
        "method": None,
        "candidate_count": 0,
        "selected_start": None,
        "selected_end": None,
        "errors": [],
    }
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
        report["errors"].append("Whole JSON response is not an object")
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    candidates: list[tuple[int, int, dict[str, Any]]] = []
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
        report["errors"].append("No mechanically parseable JSON object found")
        return None, report

    # "Final JSON" is the object whose parsed region ends last. Ties prefer the
    # outermost/earliest start. No field or value is repaired.
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
    experiment: str,
    configuration: str,
    size: int,
    run_id: str,
) -> Path:
    return (
        state_root
        / "results"
        / experiment
        / configuration
        / f"size_{size}"
        / run_id
    )


def expected_verify_command(args: argparse.Namespace) -> str:
    command = [
        sys.executable,
        "experiments/skillnet/verify_condition.py",
        "--experiment",
        args.experiment,
        "--configuration",
        args.configuration,
        "--size",
        str(args.size),
        "--run-id",
        args.run_id,
    ]
    default_root = Path(__file__).resolve().parent
    if args.state_root.resolve() != default_root:
        command.extend(["--state-root", str(args.state_root.resolve())])
    return shlex.join(command)


def task_artifact_audit(
    run_root: Path,
    task_ids: list[str],
    *,
    include_verifier_artifacts: bool,
) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, Any]]:
    missing: dict[str, list[str]] = {}
    unexpected: dict[str, list[str]] = {}
    matrix: dict[str, Any] = {}
    for task_id in task_ids:
        task_dir = run_root / task_id
        validation_path = task_dir / "schema_validation.json"
        validation = (
            runner.load_json(validation_path)
            if validation_path.is_file()
            else {"schema_valid": False}
        )
        required = runner.expected_run_artifacts(validation)
        if include_verifier_artifacts:
            required.extend(VERIFIER_REQUIRED_ARTIFACTS)
        task_missing = [
            filename
            for filename in required
            if not (task_dir / filename).is_file()
        ]
        task_unexpected: list[str] = []
        prediction_path = task_dir / "prediction.json"
        if validation.get("schema_valid") is not True and prediction_path.exists():
            task_unexpected.append("prediction.json")
        if task_missing:
            missing[task_id] = task_missing
        if task_unexpected:
            unexpected[task_id] = task_unexpected
        matrix[task_id] = {
            "schema_valid": validation.get("schema_valid") is True,
            "prediction_required": validation.get("schema_valid") is True,
            "required_artifacts": required,
            "present_artifacts": [
                filename
                for filename in required
                if (task_dir / filename).is_file()
            ],
            "missing_artifacts": task_missing,
            "unexpected_artifacts": task_unexpected,
        }
    return missing, unexpected, matrix


def write_condition_validation(
    run_root: Path,
    *,
    args: argparse.Namespace,
    status: str,
    missing: dict[str, list[str]],
    unexpected: dict[str, list[str]],
    matrix: dict[str, Any],
    evaluator_exit_code: int | None = None,
) -> None:
    runner.write_json(
        run_root / "condition_validation.json",
        {
            "schema_version": "1.0",
            "status": status,
            "experiment_id": args.experiment,
            "configuration": args.configuration,
            "catalogue_size": args.size,
            "run_id": args.run_id,
            "checked_at": runner.utc_now(),
            "missing_artifacts": missing,
            "unexpected_artifacts": unexpected,
            "task_artifact_matrix": matrix,
            "evaluator_exit_code": evaluator_exit_code,
        },
        exclusive=True,
    )


def load_post_evaluation_graph_catalogue(
    repo: Path,
    size: int,
) -> tuple[Path, dict[str, Any]]:
    path = (
        repo
        / "skillnet_run_guide_v1_1"
        / "catalogues"
        / f"size_{size}"
        / runner.CONFIGURATION_FILENAMES["C"]
    )
    catalogue = runner.load_json(path)
    if catalogue.get("configuration") != "C":
        raise RuntimeError(f"Overlay Catalogue is not C: {path}")
    if catalogue.get("catalogue_size") != size:
        raise RuntimeError(f"Overlay Catalogue size mismatch: {path}")
    if not isinstance(catalogue.get("relations"), dict):
        raise RuntimeError(f"Overlay Catalogue has no relations: {path}")
    return path, catalogue


def normalized_graph_edges(catalogue: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints = {
        "prerequisite": ("before", "after"),
        "conflict": ("gate_skill", "blocked_skill"),
        "mutex": ("skill_a", "skill_b"),
        "enhances": ("source", "target"),
    }
    edges: list[dict[str, Any]] = []
    for relation_type, records in catalogue.get("relations", {}).items():
        if relation_type not in endpoints or not isinstance(records, list):
            continue
        source_key, target_key = endpoints[relation_type]
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            source = record.get(source_key)
            target = record.get(target_key)
            if not isinstance(source, str) or not isinstance(target, str):
                continue
            edges.append(
                {
                    "edge_id": f"{relation_type}:{index}:{source}->{target}",
                    "relation_type": relation_type,
                    "source": source,
                    "target": target,
                    "attributes": {
                        key: value
                        for key, value in record.items()
                        if key not in {source_key, target_key}
                    },
                }
            )
    return edges


def build_evaluation_trace(
    *,
    args: argparse.Namespace,
    gold_task: dict[str, Any],
    prediction: dict[str, Any] | None,
    result_row: dict[str, Any],
) -> dict[str, Any]:
    predicted_sequence = (
        prediction.get("skill_sequence", []) if prediction is not None else []
    )
    selected_departments = (
        prediction.get("selected_departments", [])
        if prediction is not None
        else []
    )
    predicted_blockers = (
        prediction.get("blocked_by", []) if prediction is not None else []
    )
    predicted_route_choice = (
        prediction.get("route_choice", {}) if prediction is not None else {}
    )
    expected_blockers = gold_task.get("expected_blocked_by", [])
    missing_blockers = sorted(set(expected_blockers) - set(predicted_blockers))
    extra_blockers = sorted(set(predicted_blockers) - set(expected_blockers))
    conflict_constraints = [
        value
        for value in gold_task.get("task_constraints", [])
        if value.get("type") == "conflict_block"
    ]
    mutex_constraints = [
        value
        for value in gold_task.get("task_constraints", [])
        if value.get("type") == "mutex_route"
    ]
    primary_failure = result_row.get("primary_failure")
    secondary_failures = result_row.get("secondary_failures", [])
    return {
        "schema_version": "1.0",
        "experiment_id": args.experiment,
        "task_id": gold_task["task_id"],
        "configuration": args.configuration,
        "catalogue_size": args.size,
        "run_id": args.run_id,
        "prediction_available_to_evaluator": prediction is not None,
        "predicted_sequence": predicted_sequence,
        "skill_checks": {
            "required": gold_task.get("required_skills", []),
            "optional": gold_task.get("optional_skills", []),
            "missing": result_row.get("missing_required_skills", []),
            "extra": result_row.get("extra_skills", []),
        },
        "department_checks": {
            "selected": selected_departments,
            "required": gold_task.get("required_departments", []),
            "missing": result_row.get("missing_departments", []),
            "extra": result_row.get("extra_departments", []),
        },
        "hard_order_checks": {
            "constraints": gold_task.get("hard_order_constraints", []),
            "results": result_row.get("hard_order_results", []),
            "violations": result_row.get("unsatisfied_order_pairs", []),
            "passed": not result_row.get("unsatisfied_order_pairs", []),
        },
        "forbidden_checks": {
            "forbid_all_skills": gold_task.get("forbid_all_skills", False),
            "forbidden": gold_task.get("forbidden_skills", []),
            "hits": result_row.get("forbidden_hits", []),
            "passed": not result_row.get("forbidden_hits", []),
        },
        "conflict_checks": {
            "constraints": conflict_constraints,
            "violations": result_row.get("conflict_violations", []),
            "passed": not result_row.get("conflict_violations", []),
        },
        "mutex_checks": {
            "constraints": mutex_constraints,
            "violations": result_row.get("mutex_violations", []),
            "passed": not result_row.get("mutex_violations", []),
        },
        "final_status_check": {
            "predicted": (
                prediction.get("final_status") if prediction is not None else None
            ),
            "expected": gold_task.get("expected_final_status"),
            "passed": result_row.get("final_status_correct", False),
        },
        "route_choice_check": {
            "predicted": predicted_route_choice,
            "expected": gold_task.get("expected_route_choice", {}),
            "passed": result_row.get("route_choice_correct", False),
        },
        "blocked_checks": {
            "predicted": predicted_blockers,
            "expected": expected_blockers,
            "missing": missing_blockers,
            "extra": extra_blockers,
            "passed": not missing_blockers and not extra_blockers,
        },
        "failure_tags": {
            "primary": primary_failure,
            "secondary": secondary_failures,
            "all": (
                ([primary_failure] if primary_failure else [])
                + secondary_failures
            ),
        },
    }


def violated_graph_edges(result_row: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for record in result_row.get("unsatisfied_order_pairs", []):
        violations.append(
            {
                "relation_type": "hard_order",
                "source": record.get("before"),
                "target": record.get("after"),
                "details": record,
            }
        )
    for record in result_row.get("conflict_violations", []):
        for blocked_skill in record.get("blocked_skills_called", []):
            violations.append(
                {
                    "relation_type": "conflict",
                    "source": record.get("trigger_skill"),
                    "target": blocked_skill,
                    "details": record,
                }
            )
    for record in result_row.get("mutex_violations", []):
        hits = record.get("forbidden_route_skills_called", [])
        if hits:
            for skill in hits:
                violations.append(
                    {
                        "relation_type": "mutex_route",
                        "source": record.get("decision_id"),
                        "target": skill,
                        "details": record,
                    }
                )
        else:
            violations.append(
                {
                    "relation_type": "mutex_route",
                    "source": record.get("decision_id"),
                    "target": None,
                    "details": record,
                }
            )
    return violations


def build_graph_overlay(
    *,
    repo: Path,
    args: argparse.Namespace,
    condition_metadata: dict[str, Any],
    overlay_path: Path,
    overlay_catalogue: dict[str, Any],
    gold_task: dict[str, Any],
    prediction: dict[str, Any] | None,
    result_row: dict[str, Any],
) -> dict[str, Any]:
    sequence = prediction.get("skill_sequence", []) if prediction else []
    blocked_by = prediction.get("blocked_by", []) if prediction else []
    route_choice = prediction.get("route_choice", {}) if prediction else {}
    edges = normalized_graph_edges(overlay_catalogue)
    edge_types_by_pair: dict[tuple[str, str], list[str]] = {}
    for edge in edges:
        pair = (edge["source"], edge["target"])
        edge_types_by_pair.setdefault(pair, []).append(edge["relation_type"])
    route_edges = [
        {
            "source": source,
            "target": target,
            "relation_types": edge_types_by_pair.get(
                (source, target), ["sequence_transition"]
            ),
        }
        for source, target in zip(sequence, sequence[1:])
    ]
    visible_nodes = [
        {
            "skill_id": skill.get("skill_id"),
            "department_id": skill.get("department_id"),
            "name_en": skill.get("name_en"),
            "display_name_zh": skill.get("display_name_zh"),
        }
        for skill in runner.flatten_catalogue_skills(overlay_catalogue)
    ]
    relations = overlay_catalogue.get("relations", {})
    semantics = overlay_catalogue.get("relation_semantics", {})
    relation_types = [
        {
            "relation_type": relation_type,
            "edge_count": len(records) if isinstance(records, list) else 0,
            "semantics": semantics.get(relation_type, {}),
        }
        for relation_type, records in relations.items()
    ]
    blocked_targets = sorted(
        {
            skill_id
            for constraint in gold_task.get("task_constraints", [])
            if constraint.get("type") == "conflict_block"
            for skill_id in constraint.get("blocked_skills", [])
        }
    )
    return {
        "schema_version": "1.0",
        "post_evaluation_overlay": args.configuration in {"A", "B"},
        "relations_loaded_after_response": True,
        "overlay_catalogue_configuration": "C",
        "visible_nodes": visible_nodes,
        "visible_edges": edges,
        "selected_route": {
            "skill_sequence": sequence,
            "selected_departments": (
                prediction.get("selected_departments", []) if prediction else []
            ),
            "blocked_by": blocked_by,
            "route_choice": route_choice,
            "route_edges": route_edges,
        },
        "sequence_positions": [
            {"skill_id": skill_id, "position": index}
            for index, skill_id in enumerate(sequence, start=1)
        ],
        "gold_nodes": {
            "required": gold_task.get("required_skills", []),
            "missing": result_row.get("missing_required_skills", []),
            "extra": result_row.get("extra_skills", []),
            "forbidden": (
                [node["skill_id"] for node in visible_nodes]
                if gold_task.get("forbid_all_skills", False)
                else gold_task.get("forbidden_skills", [])
            ),
            "blocked": blocked_targets,
            "blockers": gold_task.get("expected_blocked_by", []),
        },
        "violated_edges": violated_graph_edges(result_row),
        "relation_types": relation_types,
        "metadata": {
            "experiment_id": args.experiment,
            "task_id": gold_task["task_id"],
            "configuration": args.configuration,
            "catalogue_size": args.size,
            "run_id": args.run_id,
            "runtime_repo_commit": condition_metadata.get(
                "repository_commit"
            ),
            "run_catalogue_source_commit": condition_metadata.get(
                "catalogue_source_commit"
            ),
            "overlay_catalogue_source_commit": overlay_catalogue.get(
                "source_commit"
            ),
            "overlay_catalogue_path": str(overlay_path.relative_to(repo)),
            "overlay_catalogue_sha256": runner.sha256_file(overlay_path),
            "overlay_read_phase": "after_response_and_evaluator",
        },
    }


def verify_condition(args: argparse.Namespace) -> int:
    repo = runner.repository_root()
    state_root = args.state_root.resolve()
    catalogue_path, _catalogue, task_ids = runner.resolve_condition(
        repo, args.experiment, args.configuration, args.size
    )
    run_root = runner.condition_run_root(
        state_root,
        args.experiment,
        args.configuration,
        args.size,
        args.run_id,
    )
    if not run_root.is_dir():
        raise RuntimeError(f"Condition run does not exist: {run_root}")
    condition_metadata_path = run_root / "condition_metadata.json"
    if not condition_metadata_path.is_file():
        raise RuntimeError(
            f"Missing condition metadata: {condition_metadata_path}"
        )
    condition_metadata = runner.load_json(condition_metadata_path)
    expected_identity = {
        "experiment": args.experiment,
        "configuration": args.configuration,
        "size": args.size,
        "run_id": args.run_id,
        "task_ids": task_ids,
        "catalogue_sha256": runner.sha256_file(catalogue_path),
    }
    for key, expected in expected_identity.items():
        if condition_metadata.get(key) != expected:
            raise RuntimeError(
                f"Condition metadata mismatch for {key}: "
                f"{condition_metadata.get(key)!r} != {expected!r}"
            )

    condition_validation_path = run_root / "condition_validation.json"
    if condition_validation_path.exists():
        raise RuntimeError(
            "Condition validation already exists and will not be overwritten: "
            f"{condition_validation_path}"
        )
    existing_verifier_artifacts = {
        task_id: [
            filename
            for filename in VERIFIER_REQUIRED_ARTIFACTS
            if (run_root / task_id / filename).exists()
        ]
        for task_id in task_ids
    }
    existing_verifier_artifacts = {
        task_id: filenames
        for task_id, filenames in existing_verifier_artifacts.items()
        if filenames
    }
    missing, unexpected, matrix = task_artifact_audit(
        run_root, task_ids, include_verifier_artifacts=False
    )
    for task_id, filenames in existing_verifier_artifacts.items():
        unexpected.setdefault(task_id, []).extend(filenames)
    if missing or unexpected:
        write_condition_validation(
            run_root,
            args=args,
            status="incomplete",
            missing=missing,
            unexpected=unexpected,
            matrix=matrix,
        )
        print(
            json.dumps(
                {
                    "status": "incomplete",
                    "missing_artifacts": missing,
                    "unexpected_artifacts": unexpected,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 5

    final_root = result_root(
        state_root,
        args.experiment,
        args.configuration,
        args.size,
        args.run_id,
    )
    if final_root.exists():
        raise RuntimeError(
            f"Verification result already exists and will not be overwritten: "
            f"{final_root}"
        )
    final_root.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(
        tempfile.mkdtemp(
            prefix=f".{args.run_id}.verify.",
            dir=final_root.parent,
        )
    )

    promoted = False
    try:
        predictions_dir = temp_root / "predictions"
        records_dir = temp_root / "verification_records"
        predictions_dir.mkdir()
        records_dir.mkdir()
        schema_path = runner.canonical_schema_path(repo)
        schema = runner.load_json(schema_path)
        valid_predictions = 0
        evaluated_predictions: dict[str, dict[str, Any] | None] = {}

        for task_id in task_ids:
            raw_path = run_root / task_id / "raw_response.txt"
            raw = raw_path.read_text(encoding="utf-8")
            prediction, extraction = mechanical_extract_final_object(raw)
            errors: list[dict[str, str]] = []
            if prediction is not None:
                errors = runner.schema_errors(prediction, schema, task_id)
            else:
                errors = [
                    {"path": "", "message": message}
                    for message in extraction["errors"]
                ]
            valid = prediction is not None and not errors
            record = {
                "task_id": task_id,
                "raw_response_path": str(raw_path),
                "raw_response_sha256": runner.sha256_file(raw_path),
                "extraction": extraction,
                "schema_path": str(schema_path.relative_to(repo)),
                "schema_sha256": runner.sha256_file(schema_path),
                "schema_valid": valid,
                "errors": errors,
                "included_in_predictions_directory": valid,
            }
            runner.write_json(records_dir / f"{task_id}.json", record)
            if valid:
                runner.write_json(
                    predictions_dir / f"{task_id}.json", prediction
                )
                evaluated_predictions[task_id] = prediction
                valid_predictions += 1
            else:
                evaluated_predictions[task_id] = None

        prediction_entries = sorted(predictions_dir.iterdir())
        if any(
            not path.is_file() or path.suffix != ".json"
            for path in prediction_entries
        ):
            raise RuntimeError(
                "Predictions directory isolation check failed"
            )

        if args.experiment == "E1":
            validate_frozen_e1_gold(repo)
            gold_path = frozen_e1_gold_path()
        else:
            gold_path = full_gold_path(repo)

        # Promote only the input/verification material first. Evaluator paths
        # then point at their permanent locations, so unmodified evaluator
        # output never contains stale temporary paths.
        os.rename(temp_root, final_root)
        promoted = True
        predictions_dir = final_root / "predictions"
        records_dir = final_root / "verification_records"
        evaluator_output_dir = final_root / "evaluator_output"

        gold_validation_output = final_root / "gold_validation.json"
        gold_validation_command = [
            sys.executable,
            str(evaluator_path(repo)),
            "validate-package",
            "--gold",
            str(gold_path),
            "--output",
            str(gold_validation_output),
        ]
        gold_validation_process = subprocess.run(
            gold_validation_command,
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        gold_validation_invocation = {
            "command": gold_validation_command,
            "stdout": gold_validation_process.stdout,
            "stderr": gold_validation_process.stderr,
            "exit_code": gold_validation_process.returncode,
        }
        runner.write_json(
            final_root / "gold_validation_invocation.json",
            gold_validation_invocation,
        )
        if gold_validation_process.returncode != 0:
            raise RuntimeError(
                "Gold package validation failed; evaluator was not run"
            )

        evaluator_command = [
            sys.executable,
            str(evaluator_path(repo)),
            "evaluate",
            "--gold",
            str(gold_path),
            "--predictions",
            str(predictions_dir),
            "--configuration",
            args.configuration,
            "--run-id",
            args.run_id,
            "--output-dir",
            str(evaluator_output_dir),
        ]
        evaluator_process = subprocess.run(
            evaluator_command,
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        evaluator_invocation = {
            "command": evaluator_command,
            "stdout": evaluator_process.stdout,
            "stderr": evaluator_process.stderr,
            "exit_code": evaluator_process.returncode,
        }
        runner.write_json(
            final_root / "evaluator_invocation.json",
            evaluator_invocation,
        )

        per_task_results_path = (
            evaluator_output_dir / "per_task_results.json"
        )
        if not per_task_results_path.is_file():
            missing, unexpected, matrix = task_artifact_audit(
                run_root, task_ids, include_verifier_artifacts=True
            )
            write_condition_validation(
                run_root,
                args=args,
                status="incomplete",
                missing=missing,
                unexpected=unexpected,
                matrix=matrix,
                evaluator_exit_code=evaluator_process.returncode,
            )
            return 5
        result_rows = runner.load_json(per_task_results_path)
        if not isinstance(result_rows, list):
            raise RuntimeError("Evaluator per-task results must be a JSON list")
        rows_by_task = {
            row.get("task_id"): row
            for row in result_rows
            if isinstance(row, dict)
        }
        if len(rows_by_task) != len(result_rows):
            raise RuntimeError("Evaluator per-task results contain duplicates")
        if set(rows_by_task) != set(task_ids):
            raise RuntimeError(
                "Evaluator per-task result IDs do not match the condition: "
                f"{sorted(rows_by_task)}"
            )
        gold = runner.load_json(gold_path)
        gold_by_task = {
            task["task_id"]: task for task in gold.get("tasks", [])
        }
        if set(gold_by_task) != set(task_ids):
            raise RuntimeError("Gold task IDs do not match the condition")

        # For A/B, this is the first read of the same-size C Catalogue. It is
        # intentionally after every response has been recorded and after the
        # deterministic evaluator has returned.
        overlay_path, overlay_catalogue = load_post_evaluation_graph_catalogue(
            repo, args.size
        )
        for task_id in task_ids:
            task_dir = run_root / task_id
            result_row = rows_by_task[task_id]
            prediction = evaluated_predictions[task_id]
            runner.write_json(
                task_dir / "evaluation_trace.json",
                build_evaluation_trace(
                    args=args,
                    gold_task=gold_by_task[task_id],
                    prediction=prediction,
                    result_row=result_row,
                ),
                exclusive=True,
            )
            runner.write_json(
                task_dir / "graph_overlay.json",
                build_graph_overlay(
                    repo=repo,
                    args=args,
                    condition_metadata=condition_metadata,
                    overlay_path=overlay_path,
                    overlay_catalogue=overlay_catalogue,
                    gold_task=gold_by_task[task_id],
                    prediction=prediction,
                    result_row=result_row,
                ),
                exclusive=True,
            )
            # Copy the deterministic evaluator row JSON-value-for-value without
            # repairing, enriching, or reformatting any model field.
            runner.write_json(
                task_dir / "result_row.json",
                result_row,
                exclusive=True,
            )

        missing, unexpected, matrix = task_artifact_audit(
            run_root, task_ids, include_verifier_artifacts=True
        )
        contract_status = (
            "complete" if not missing and not unexpected else "incomplete"
        )
        write_condition_validation(
            run_root,
            args=args,
            status=contract_status,
            missing=missing,
            unexpected=unexpected,
            matrix=matrix,
            evaluator_exit_code=evaluator_process.returncode,
        )

        verify_command = expected_verify_command(args)
        (final_root / "VERIFY_COMMAND.txt").write_text(
            f"VERIFY COMMAND: {verify_command}\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": "1.0",
            "experiment": args.experiment,
            "configuration": args.configuration,
            "size": args.size,
            "run_id": args.run_id,
            "task_ids": task_ids,
            "source_run_root": str(run_root),
            "catalogue_path": str(catalogue_path.relative_to(repo)),
            "catalogue_sha256": runner.sha256_file(catalogue_path),
            "gold_path": str(gold_path.relative_to(repo)),
            "gold_sha256": runner.sha256_file(gold_path),
            "prediction_schema_sha256": runner.sha256_file(schema_path),
            "raw_response_count": len(task_ids),
            "valid_prediction_count": valid_predictions,
            "invalid_prediction_count": len(task_ids) - valid_predictions,
            "predictions_directory_contains_only_prediction_json": True,
            "evaluator_exit_code": evaluator_process.returncode,
            "artifact_contract_status": contract_status,
            "missing_artifacts": missing,
            "unexpected_artifacts": unexpected,
            "verify_command": verify_command,
        }
        runner.write_json(final_root / "verification_manifest.json", manifest)
    except Exception:
        if not promoted:
            shutil.rmtree(temp_root, ignore_errors=True)
        if not condition_validation_path.exists():
            missing, unexpected, matrix = task_artifact_audit(
                run_root, task_ids, include_verifier_artifacts=True
            )
            write_condition_validation(
                run_root,
                args=args,
                status="incomplete",
                missing=missing,
                unexpected=unexpected,
                matrix=matrix,
                evaluator_exit_code=(
                    evaluator_process.returncode
                    if "evaluator_process" in locals()
                    else None
                ),
            )
        raise

    print(f"VERIFY COMMAND: {expected_verify_command(args)}")
    print(
        json.dumps(
            {
                "result_root": str(final_root),
                "valid_predictions": valid_predictions,
                "task_count": len(task_ids),
                "evaluator_exit_code": evaluator_process.returncode,
                "artifact_contract_status": contract_status,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if contract_status != "complete":
        return 5
    return evaluator_process.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepare-e1-gold",
        action="store_true",
        help="Mechanically create and validate the frozen 21-task E1 Gold.",
    )
    parser.add_argument("--experiment", choices=("E0", "E1"))
    parser.add_argument("--configuration", choices=("A", "B", "C"))
    parser.add_argument("--size", type=int)
    parser.add_argument("--run-id")
    parser.add_argument(
        "--state-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = runner.repository_root()
    if args.prepare_e1_gold:
        if any(
            value is not None
            for value in (
                args.experiment,
                args.configuration,
                args.size,
                args.run_id,
            )
        ):
            raise SystemExit(
                "--prepare-e1-gold cannot be combined with condition arguments"
            )
        report = prepare_frozen_e1_gold(repo)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    missing = [
        name
        for name, value in (
            ("--experiment", args.experiment),
            ("--configuration", args.configuration),
            ("--size", args.size),
            ("--run-id", args.run_id),
        )
        if value is None
    ]
    if missing:
        raise SystemExit(
            f"Condition verification requires: {', '.join(missing)}"
        )
    if not runner.RUN_ID_PATTERN.fullmatch(args.run_id):
        raise SystemExit(
            "run_id must match [A-Za-z0-9][A-Za-z0-9._-]*"
        )
    return verify_condition(args)


if __name__ == "__main__":
    raise SystemExit(main())
