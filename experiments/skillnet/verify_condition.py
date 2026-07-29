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


E1_GOLD_FILENAME = "E1_Gold_5_tasks.json"
E1_VALIDATION_FILENAME = "E1_Gold_5_tasks_validation.json"


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


def expected_e1_subset(repo: Path) -> dict[str, Any]:
    source_path = full_gold_path(repo)
    e1_manifest_path = manifest_path(repo)
    source = runner.load_json(source_path)
    manifest = runner.load_json(e1_manifest_path)
    task_ids = manifest.get("task_ids", [])
    if not isinstance(task_ids, list) or len(task_ids) != 5:
        raise ValueError("E1 manifest must contain exactly five task IDs")

    source_tasks = source.get("tasks", [])
    by_id = {task.get("task_id"): task for task in source_tasks}
    if len(by_id) != len(source_tasks):
        raise ValueError("Full Gold contains duplicate task IDs")
    missing = [task_id for task_id in task_ids if task_id not in by_id]
    if missing:
        raise ValueError(f"E1 manifest tasks missing from full Gold: {missing}")

    subset = copy.deepcopy(source)
    subset["task_count"] = len(task_ids)
    subset["tasks"] = [copy.deepcopy(by_id[task_id]) for task_id in task_ids]
    subset["subset_provenance"] = {
        "source_gold_path": str(source_path.relative_to(repo)),
        "source_gold_sha256": runner.sha256_file(source_path),
        "source_gold_task_count": len(source_tasks),
        "manifest_path": str(e1_manifest_path.relative_to(repo)),
        "manifest_sha256": runner.sha256_file(e1_manifest_path),
        "task_ids": task_ids,
        "task_records_copied_without_modification": True,
    }
    return subset


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
                "E1 Gold subset failed evaluator validation: "
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
    subset = expected_e1_subset(repo)
    output = frozen_e1_gold_path()
    install_if_absent_or_identical(output, stable_json_bytes(subset))

    source = runner.load_json(full_gold_path(repo))
    source_by_id = {task["task_id"]: task for task in source["tasks"]}
    for task in subset["tasks"]:
        if task != source_by_id[task["task_id"]]:
            raise RuntimeError(
                f"E1 task record changed during extraction: {task['task_id']}"
            )

    validation_path = frozen_eval_dir() / E1_VALIDATION_FILENAME
    validation = run_gold_validation(repo, output, validation_path)
    return {
        "gold_path": str(output),
        "gold_sha256": runner.sha256_file(output),
        "source_gold_sha256": subset["subset_provenance"][
            "source_gold_sha256"
        ],
        "manifest_sha256": subset["subset_provenance"]["manifest_sha256"],
        "task_ids": subset["subset_provenance"]["task_ids"],
        "validation_path": str(validation_path),
        "validation": validation["report"],
    }


def validate_frozen_e1_gold(repo: Path) -> dict[str, Any]:
    path = frozen_e1_gold_path()
    if not path.is_file():
        raise RuntimeError(
            f"Missing frozen E1 Gold subset; run --prepare-e1-gold: {path}"
        )
    actual = runner.load_json(path)
    expected = expected_e1_subset(repo)
    if actual != expected:
        raise RuntimeError(
            "Frozen E1 Gold subset no longer matches the current full Gold "
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

    missing_raw = [
        task_id
        for task_id in task_ids
        if not (run_root / task_id / "raw_response.txt").is_file()
    ]
    if missing_raw:
        raise RuntimeError(
            "Condition is incomplete; finish recording it before verification. "
            f"Missing raw responses: {missing_raw}"
        )

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
                valid_predictions += 1

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
            "verify_command": verify_command,
        }
        runner.write_json(final_root / "verification_manifest.json", manifest)
    except Exception:
        if not promoted:
            shutil.rmtree(temp_root, ignore_errors=True)
        raise

    print(f"VERIFY COMMAND: {expected_verify_command(args)}")
    print(
        json.dumps(
            {
                "result_root": str(final_root),
                "valid_predictions": valid_predictions,
                "task_count": len(task_ids),
                "evaluator_exit_code": evaluator_process.returncode,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return evaluator_process.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepare-e1-gold",
        action="store_true",
        help="Mechanically create and validate the frozen five-task E1 Gold.",
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
