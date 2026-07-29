#!/usr/bin/env python3
"""Run isolated SkillNet routing experiments with Codex."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


VALID_CONFIGURATIONS = {"A", "B", "C"}
VALID_STATUS = {"completed", "blocked", "no_tool"}
REQUIRED_PREDICTION_FIELDS = {
    "task_id",
    "use_skills",
    "selected_departments",
    "skill_sequence",
    "final_status",
    "blocked_by",
    "route_choice",
    "reason",
}
CONTROL_PROMPT = (
    "Read task.txt and the available Skill metadata. Use any advisory file named by "
    "AGENTS.md, then independently select the applicable enterprise Skills and their "
    "order. Use exact English YAML Skill slugs. Do not execute the business workflow. "
    "Return only the JSON object requested by task.txt."
)


def prepare_candidate_workspace(
    *,
    repo_root: Path,
    package_root: Path,
    configuration: str,
    task_prompt_path: Path,
    destination: Path,
) -> Path:
    """Create one Gold-free candidate workspace for one independent task."""
    if configuration not in VALID_CONFIGURATIONS:
        raise ValueError(f"unknown configuration: {configuration}")
    if destination.exists():
        raise FileExistsError(destination)

    destination.mkdir(parents=True)
    shutil.copytree(repo_root / ".agents" / "skills", destination / ".agents" / "skills")
    config_root = package_root / "configurations" / configuration
    shutil.copy2(config_root / "AGENTS.md", destination / "AGENTS.md")
    shutil.copy2(task_prompt_path, destination / "task.txt")

    if configuration == "B":
        shutil.copy2(config_root / "department_groups.json", destination / "department_groups.json")
    elif configuration == "C":
        shutil.copy2(config_root / "skill_relations.json", destination / "skill_relations.json")
    return destination


def build_codex_command(
    *,
    codex_executable: Path,
    workspace: Path,
    schema_path: Path,
    output_path: Path,
    model: str,
    reasoning_effort: str,
    prompt: str,
) -> List[str]:
    """Return the fixed, isolated Codex CLI invocation used for every trial."""
    return [
        str(codex_executable),
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "--cd",
        str(workspace),
        prompt,
    ]


def validate_prediction(prediction: Any, expected_task_id: str) -> Dict[str, Any]:
    """Validate the boundary contract before a prediction reaches the evaluator."""
    if not isinstance(prediction, dict):
        raise ValueError("prediction must be a JSON object")
    missing = sorted(REQUIRED_PREDICTION_FIELDS - set(prediction))
    if missing:
        raise ValueError(f"prediction is missing fields: {missing}")
    if prediction.get("task_id") != expected_task_id:
        raise ValueError(
            f"prediction task_id {prediction.get('task_id')!r} does not match {expected_task_id!r}"
        )
    if not isinstance(prediction.get("use_skills"), bool):
        raise ValueError("use_skills must be a boolean")
    for field in ("selected_departments", "skill_sequence", "blocked_by"):
        value = prediction.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"{field} must be an array of strings")
    if prediction.get("final_status") not in VALID_STATUS:
        raise ValueError("final_status is invalid")
    route_choice = prediction.get("route_choice")
    if not isinstance(route_choice, dict) or not all(
        isinstance(key, str) and (isinstance(value, str) or value is None)
        for key, value in route_choice.items()
    ):
        raise ValueError("route_choice must be an object of string or null values")
    if not isinstance(prediction.get("reason"), str):
        raise ValueError("reason must be a string")
    return {
        **prediction,
        "route_choice": {
            key: value for key, value in route_choice.items() if value is not None
        },
    }


def build_run_manifest(
    *,
    configuration: str,
    run_id: str,
    task_ids: Iterable[str],
    model: str,
    reasoning_effort: str,
    codex_version: str,
    max_workers: int,
) -> Dict[str, Any]:
    return {
        "configuration": configuration,
        "run_id": str(run_id),
        "task_ids": list(task_ids),
        "model": model,
        "reasoning_effort": reasoning_effort,
        "codex_version": codex_version,
        "max_workers": max_workers,
        "sandbox": "read-only",
        "independent_ephemeral_sessions": True,
        "ignore_user_config": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def load_tasks(gold_path: Path) -> Dict[str, Dict[str, Any]]:
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    return {task["task_id"]: task for task in gold["tasks"]}


def error_prediction(task_id: str, message: str) -> Dict[str, Any]:
    """Return a schema-valid record that remains an obvious evaluation failure."""
    return {
        "task_id": task_id,
        "use_skills": False,
        "selected_departments": [],
        "skill_sequence": [],
        "final_status": "no_tool",
        "blocked_by": [],
        "route_choice": {},
        "reason": f"RUNNER_ERROR: {message}",
        "runner_error": message,
    }


def normalize_subprocess_output(value: Any) -> str:
    """Return serializable text for normal and timeout subprocess streams."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def run_single_task(
    *,
    repo_root: Path,
    package_root: Path,
    configuration: str,
    task_id: str,
    codex_executable: Path,
    model: str,
    reasoning_effort: str,
    timeout_seconds: int,
    output_dir: Path,
    overwrite: bool,
) -> Dict[str, Any]:
    prediction_path = output_dir / f"{task_id}.json"
    log_dir = output_dir / ".logs"
    log_path = log_dir / f"{task_id}.log"
    if prediction_path.exists() and not overwrite:
        validate_prediction(json.loads(prediction_path.read_text(encoding="utf-8")), task_id)
        return {"task_id": task_id, "status": "skipped", "prediction": str(prediction_path)}

    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = package_root / "prompts" / f"{task_id}.txt"
    schema_path = package_root / "evaluation" / "prediction_schema.json"
    attempts: List[Dict[str, Any]] = []
    prediction: Dict[str, Any] | None = None

    for attempt in (1, 2):
        with tempfile.TemporaryDirectory(prefix=f"skillnet-{configuration}-{task_id}-") as temp:
            temp_root = Path(temp)
            workspace = prepare_candidate_workspace(
                repo_root=repo_root,
                package_root=package_root,
                configuration=configuration,
                task_prompt_path=prompt_path,
                destination=temp_root / "candidate",
            )
            raw_output = temp_root / "last_message.json"
            command = build_codex_command(
                codex_executable=codex_executable,
                workspace=workspace,
                schema_path=schema_path,
                output_path=raw_output,
                model=model,
                reasoning_effort=reasoning_effort,
                prompt=CONTROL_PROMPT,
            )
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
                attempt_record = {
                    "attempt": attempt,
                    "returncode": completed.returncode,
                    "stdout": normalize_subprocess_output(completed.stdout),
                    "stderr": normalize_subprocess_output(completed.stderr),
                }
                attempts.append(attempt_record)
                if completed.returncode != 0:
                    continue
                if not raw_output.is_file():
                    attempt_record["validation_error"] = "Codex did not write the final message"
                    continue
                try:
                    candidate = json.loads(raw_output.read_text(encoding="utf-8"))
                    prediction = validate_prediction(candidate, task_id)
                    break
                except Exception as exc:
                    attempt_record["validation_error"] = str(exc)
            except subprocess.TimeoutExpired as exc:
                attempts.append(
                    {
                        "attempt": attempt,
                        "returncode": "timeout",
                        "stdout": normalize_subprocess_output(exc.stdout),
                        "stderr": normalize_subprocess_output(exc.stderr),
                    }
                )

    if prediction is None:
        last = attempts[-1] if attempts else {}
        detail = last.get("validation_error") or last.get("stderr") or str(last.get("returncode"))
        prediction = error_prediction(task_id, str(detail).strip()[:500])
        status = "error"
    else:
        status = "completed"

    prediction_path.write_text(
        json.dumps(prediction, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    log_path.write_text(
        json.dumps({"task_id": task_id, "attempts": attempts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"task_id": task_id, "status": status, "prediction": str(prediction_path)}


def codex_version(codex_executable: Path) -> str:
    completed = subprocess.run(
        [str(codex_executable), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (completed.stdout or completed.stderr).strip()


def run_configuration(
    *,
    repo_root: Path,
    package_root: Path,
    configuration: str,
    task_ids: List[str],
    codex_executable: Path,
    model: str,
    reasoning_effort: str,
    run_id: str,
    max_workers: int,
    timeout_seconds: int,
    output_root: Path,
    overwrite: bool,
) -> Dict[str, Any]:
    output_dir = output_root / configuration / f"run_{run_id.zfill(2) if run_id.isdigit() else run_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                run_single_task,
                repo_root=repo_root,
                package_root=package_root,
                configuration=configuration,
                task_id=task_id,
                codex_executable=codex_executable,
                model=model,
                reasoning_effort=reasoning_effort,
                timeout_seconds=timeout_seconds,
                output_dir=output_dir,
                overwrite=overwrite,
            ): task_id
            for task_id in task_ids
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps({"configuration": configuration, **result}, ensure_ascii=False), flush=True)

    manifest = build_run_manifest(
        configuration=configuration,
        run_id=run_id,
        task_ids=task_ids,
        model=model,
        reasoning_effort=reasoning_effort,
        codex_version=codex_version(codex_executable),
        max_workers=max_workers,
    )
    manifest["results"] = sorted(results, key=lambda item: item["task_id"])
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--configuration",
        choices=[*sorted(VALID_CONFIGURATIONS), "ALL"],
        required=True,
    )
    parser.add_argument("--tasks", nargs="*")
    parser.add_argument("--run-id", default="1")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--codex")
    parser.add_argument("--output-root")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    package_root = Path(__file__).resolve().parents[1]
    repo_root = package_root.parent
    gold_path = package_root / "02_Gold_Standard_21_V4.json"
    tasks = load_tasks(gold_path)
    task_ids = args.tasks or list(tasks)
    unknown = sorted(set(task_ids) - set(tasks))
    if unknown:
        parser.error(f"unknown task IDs: {unknown}")
    if args.max_workers < 1:
        parser.error("--max-workers must be positive")

    executable = Path(args.codex or shutil.which("codex") or "")
    if not str(executable) or not executable.is_file():
        parser.error("Codex executable was not found; pass --codex")
    output_root = Path(args.output_root) if args.output_root else package_root / "predictions"
    configurations = sorted(VALID_CONFIGURATIONS) if args.configuration == "ALL" else [args.configuration]
    for configuration in configurations:
        run_configuration(
            repo_root=repo_root,
            package_root=package_root,
            configuration=configuration,
            task_ids=task_ids,
            codex_executable=executable,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            run_id=str(args.run_id),
            max_workers=args.max_workers,
            timeout_seconds=args.timeout_seconds,
            output_root=output_root,
            overwrite=args.overwrite,
        )


if __name__ == "__main__":
    main()
