#!/usr/bin/env python3
"""Run one non-benchmark synthetic Codex transport/JSON Setup smoke."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import run_condition as runner


EXPECTED_KEYS = {
    "task_id",
    "use_skills",
    "selected_departments",
    "skill_sequence",
    "final_status",
    "blocked_by",
    "route_choice",
    "reason",
}


def validate(value: Any) -> list[str]:
    errors = []
    if not isinstance(value, dict):
        return ["response_not_object"]
    if set(value) != EXPECTED_KEYS:
        errors.append("exact_key_set_mismatch")
    expected_types = {
        "task_id": str,
        "use_skills": bool,
        "selected_departments": list,
        "skill_sequence": list,
        "final_status": str,
        "blocked_by": list,
        "route_choice": dict,
        "reason": str,
    }
    for key, expected_type in expected_types.items():
        if key in value and not isinstance(value[key], expected_type):
            errors.append(f"{key}_wrong_type")
    for key in ("selected_departments", "skill_sequence", "blocked_by"):
        if isinstance(value.get(key), list) and not all(
            isinstance(item, str) for item in value[key]
        ):
            errors.append(f"{key}_item_wrong_type")
    if isinstance(value.get("route_choice"), dict) and not all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in value["route_choice"].items()
    ):
        errors.append("route_choice_item_wrong_type")
    status = value.get("final_status")
    if status not in {"completed", "blocked", "no_tool"}:
        errors.append("invalid_final_status")
    if status == "completed" and (
        value.get("use_skills") is not True or value.get("blocked_by") != []
    ):
        errors.append("completed_inconsistent")
    if status == "blocked" and (
        value.get("use_skills") is not True
        or not value.get("blocked_by")
        or value.get("skill_sequence") != []
    ):
        errors.append("blocked_inconsistent")
    if status == "no_tool" and (
        value.get("use_skills") is not False
        or value.get("selected_departments") != []
        or value.get("skill_sequence") != []
        or value.get("blocked_by") != []
        or value.get("route_choice") != {}
    ):
        errors.append("no_tool_inconsistent")
    if value.get("task_id") != "SYNTHETIC_E1V2_SETUP":
        errors.append("task_id_mismatch")
    if not isinstance(value.get("reason"), str) or not value.get(
        "reason", ""
    ).strip():
        errors.append("empty_reason")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-id", required=True)
    args = parser.parse_args()
    repo = runner.repository_root()
    output = (
        Path(__file__).resolve().parent
        / "setup_evidence"
        / "synthetic_smoke"
        / args.smoke_id
    )
    if output.exists():
        raise SystemExit(f"Smoke evidence exists: {output}")
    output.mkdir(parents=True)
    raw_path = output / "raw_response.txt"
    events_path = output / "codex_events.jsonl"
    prompt = """This is a synthetic transport and JSON-format smoke test.
It is not a benchmark task, contains no Gold, and contains no Skill Catalogue.
Do not use tools or read files. Return exactly one JSON object and no other text.

Use exactly these eight keys and types:
- task_id: string, exactly "SYNTHETIC_E1V2_SETUP"
- use_skills: boolean
- selected_departments: array of strings
- skill_sequence: array of strings
- final_status: one of "completed", "blocked", "no_tool"
- blocked_by: array of strings
- route_choice: object whose keys and values are strings
- reason: non-empty string

For this synthetic request, choose no_tool. Status rules:
- completed requires use_skills=true and blocked_by=[]
- blocked requires use_skills=true, at least one blocked_by string, and skill_sequence=[]
- no_tool requires use_skills=false and selected_departments=[], skill_sequence=[],
  blocked_by=[], route_choice={}
"""
    with tempfile.TemporaryDirectory(
        prefix="skillnet_e1v2_synthetic_"
    ) as temporary:
        command = [
            str(runner.PINNED_CODEX_PATH),
            "exec",
            "--ignore-user-config",
            "--ignore-rules",
            "--strict-config",
            "--ephemeral",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "--model",
            runner.PINNED_MODEL,
            "-c",
            f'model_reasoning_effort="{runner.PINNED_REASONING_EFFORT}"',
            "--color",
            "never",
            "--json",
            "--cd",
            temporary,
            "--output-last-message",
            str(raw_path),
            "-",
        ]
        process = subprocess.run(
            command,
            input=prompt.encode("utf-8"),
            capture_output=True,
            check=False,
        )
    events_path.write_bytes(process.stdout)
    if not raw_path.exists():
        raw_path.write_bytes(b"")
    event_errors = []
    for line_number, line in enumerate(
        process.stdout.decode("utf-8", errors="replace").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            event_errors.append(f"line_{line_number}:{exc}")
    response_errors = []
    try:
        response = json.loads(raw_path.read_text(encoding="utf-8"))
    except Exception as exc:
        response = None
        response_errors.append(f"direct_json_parse:{exc}")
    if response is not None:
        response_errors.extend(validate(response))
    version = runner.codex_version(runner.PINNED_CODEX_PATH)
    valid = (
        process.returncode == 0
        and version == runner.PINNED_CODEX_VERSION
        and not event_errors
        and not response_errors
    )
    validation = {
        "schema_version": "E1V2-1.0",
        "experiment_id": "E1V2",
        "smoke_id": args.smoke_id,
        "synthetic_only": True,
        "contains_gold_task": False,
        "contains_catalogue": False,
        "formal_model_task": False,
        "fresh_codex_process_count": 1,
        "command": command,
        "codex_version": version,
        "expected_codex_version": runner.PINNED_CODEX_VERSION,
        "exit_code": process.returncode,
        "stderr": process.stderr.decode("utf-8", errors="replace"),
        "event_json_errors": event_errors,
        "response_errors": response_errors,
        "raw_response_sha256": runner.sha256_file(raw_path),
        "codex_events_sha256": runner.sha256_file(events_path),
        "valid": valid,
    }
    runner.write_json(output / "validation.json", validation)
    runner.write_bytes(output / "prompt.txt", prompt.encode("utf-8"))
    runner.write_bytes(
        output / "stderr.txt",
        process.stderr,
    )
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
