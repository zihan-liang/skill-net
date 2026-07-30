#!/usr/bin/env python3
"""Validate the frozen E4 Chinese prompts and their provenance contracts.

The mechanical checks in this module deliberately do not claim semantic
equivalence.  Route, blocker, mutex, acceptance, and no-tool preservation are
accepted only when the per-task human audit is complete and marked passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SEMANTIC_CONTRACT_FIELDS = (
    "initial_skill_states",
    "required_skills",
    "optional_skills",
    "forbidden_skills",
    "forbid_all_skills",
    "hard_order_constraints",
    "expected_final_status",
    "expected_blocked_by",
    "expected_route_choice",
    "task_constraints",
)

AUDIT_FIELDS = (
    "current_state_facts_preserved",
    "high_level_goal_preserved",
    "stop_boundary_preserved",
    "unique_route_preserved",
    "blocked_condition_preserved",
    "mutex_condition_preserved",
    "acceptance_route_preserved",
    "no_tool_intent_preserved",
    "process_name_leakage_check",
    "ordered_step_leakage_check",
    "reviewer_status",
    "reviewer_notes",
)

STATUS_AUDIT_FIELDS = (
    "stop_boundary_preserved",
    "unique_route_preserved",
    "blocked_condition_preserved",
    "mutex_condition_preserved",
    "acceptance_route_preserved",
    "no_tool_intent_preserved",
    "process_name_leakage_check",
    "ordered_step_leakage_check",
)

EXPERIMENTAL_LANGUAGE_PATTERNS = (
    re.compile(r"请调用以下\s*Skills?", re.IGNORECASE),
    re.compile(r"请(?:规划|列出|返回|给出).{0,8}(?:Skills?|技能)(?:列表|序列|路径)?", re.IGNORECASE),
    re.compile(r"required[_ ]skills", re.IGNORECASE),
    re.compile(r"canonical(?:\s+English)?\s+Skill", re.IGNORECASE),
)

EXPLICIT_ENUMERATION_PATTERNS = (
    re.compile(r"(?:^|\n)\s*(?:\d+[.)、]|[一二三四五六七八九十]+[、.)）])"),
    re.compile(r"(?:→|->|=>|⇒)"),
    re.compile(r"第一.{0,80}第二"),
    re.compile(r"先.{0,80}然后.{0,80}最后"),
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_contract(task: dict[str, Any]) -> dict[str, Any]:
    return {field: task.get(field) for field in SEMANTIC_CONTRACT_FIELDS}


def semantic_contract_sha256(task: dict[str, Any]) -> str:
    return stable_json_sha256(semantic_contract(task))


def sentence_count(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    terminators = re.findall(r"[。！？!?]+", stripped)
    return len(terminators) if terminators else 1


def extract_chinese_prompt(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0] if text else ""
    if not first_line.startswith("Task ID: "):
        raise ValueError(f"Missing Task ID header: {path}")
    task_id = first_line.removeprefix("Task ID: ").strip()
    marker = "\n中文任务\n"
    end_marker = "\n\nOutput requirements"
    if marker not in text or end_marker not in text:
        raise ValueError(f"Cannot isolate Chinese prompt: {path}")
    prompt = text.split(marker, 1)[1].split(end_marker, 1)[0].strip()
    if not prompt:
        raise ValueError(f"Empty Chinese prompt: {path}")
    return task_id, prompt


def error(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def display_name_map(repo: Path | None = None) -> dict[str, str]:
    root = repo or repository_root()
    mapping = load_json(root / "SkillNet_Gold_Tasks_V4" / "skill_name_map.json")
    return {item["id"]: item["display_name"] for item in mapping["skills"]}


def validate_prompt_text(
    prompt: str,
    gold_task: dict[str, Any],
    gold_package: dict[str, Any],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    count = sentence_count(prompt)
    if count not in {1, 2}:
        errors.append(error("sentence_count", f"expected 1-2 sentences, found {count}"))
    if not re.search(r"[\u3400-\u9fff]", prompt):
        errors.append(error("language", "prompt contains no Chinese text"))

    skill_ids = sorted(gold_package.get("skill_catalog", {}), key=len, reverse=True)
    leaked_skills = [skill_id for skill_id in skill_ids if skill_id in prompt]
    if leaked_skills:
        errors.append(
            error("canonical_skill_id_leakage", f"canonical Skill IDs: {leaked_skills}")
        )
    department_ids = gold_package.get("department_catalog", [])
    leaked_departments = [value for value in department_ids if value in prompt]
    if leaked_departments:
        errors.append(
            error("department_id_leakage", f"department IDs: {leaked_departments}")
        )
    if any(pattern.search(prompt) for pattern in EXPERIMENTAL_LANGUAGE_PATTERNS):
        errors.append(error("experimental_language", "experimental routing language found"))
    if any(pattern.search(prompt) for pattern in EXPLICIT_ENUMERATION_PATTERNS):
        errors.append(error("explicit_step_enumeration", "explicit ordered steps found"))

    department_names = ("业务部门", "财务部门", "采购部门", "技术部门", "人力资源部门")
    named_departments = [name for name in department_names if name in prompt]
    if len(named_departments) > 1:
        errors.append(error("department_list", f"department list: {named_departments}"))

    names = display_name_map()
    ordered_mentions: list[tuple[int, str, str]] = []
    for skill_id in gold_task.get("required_skills", []):
        name = names.get(skill_id)
        if name and name in prompt:
            ordered_mentions.append((prompt.index(name), skill_id, name))
    if len(ordered_mentions) >= 2:
        positions = [item[0] for item in ordered_mentions]
        if positions == sorted(positions):
            errors.append(
                error(
                    "required_order_name_leakage",
                    "multiple formal Chinese Skill names repeat required order: "
                    + ", ".join(item[2] for item in ordered_mentions),
                )
            )
    return errors


def validate_audit_task(record: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for field in AUDIT_FIELDS:
        if field not in record:
            errors.append(error("missing_audit_field", field))
    facts = record.get("current_state_facts_preserved")
    if "current_state_facts_preserved" in record and (
        not isinstance(facts, list)
        or not facts
        or any(not isinstance(item, str) or not item.strip() for item in facts)
    ):
        errors.append(error("invalid_audit_field", "current_state_facts_preserved"))
    goal = record.get("high_level_goal_preserved")
    if "high_level_goal_preserved" in record and (
        not isinstance(goal, str) or not goal.strip()
    ):
        errors.append(error("invalid_audit_field", "high_level_goal_preserved"))
    for field in STATUS_AUDIT_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if not isinstance(value, dict):
            errors.append(error("invalid_audit_field", field))
            continue
        allowed = {"pass", "not_applicable"}
        if value.get("status") not in allowed:
            errors.append(error("audit_not_passed", field))
        evidence = value.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            errors.append(error("invalid_audit_field", f"{field}.evidence"))
    if record.get("reviewer_status") != "pass":
        errors.append(error("audit_not_passed", "reviewer_status"))
    notes = record.get("reviewer_notes")
    if "reviewer_notes" in record and (not isinstance(notes, str) or not notes.strip()):
        errors.append(error("invalid_audit_field", "reviewer_notes"))
    return errors


def validate_semantic_contract(
    manifest_record: dict[str, Any],
    gold_task: dict[str, Any],
) -> list[dict[str, str]]:
    expected = semantic_contract_sha256(gold_task)
    actual = manifest_record.get("semantic_contract_sha256")
    if actual != expected:
        return [
            error(
                "semantic_contract_sha256_mismatch",
                f"manifest={actual!r}, canonical={expected!r}",
            )
        ]
    return []


def prompt_set_sha256(records: list[dict[str, Any]]) -> str:
    payload = [
        {"task_id": record["task_id"], "e4_prompt_sha256": record["e4_prompt_sha256"]}
        for record in records
    ]
    return stable_json_sha256(payload)


def validate_repository(repo: Path | None = None) -> dict[str, Any]:
    root = (repo or repository_root()).resolve()
    e4_dir = root / "experiments" / "skillnet" / "e4"
    manifest_path = e4_dir / "E4_prompt_manifest.json"
    audit_path = e4_dir / "E4_semantic_audit.json"
    gold_path = root / "SkillNet_Gold_Tasks_V4" / "02_Gold_Standard_21_V4.json"
    errors: list[dict[str, str]] = []
    task_rows: list[dict[str, Any]] = []

    if not manifest_path.is_file():
        return {"valid": False, "errors": [error("missing_manifest", str(manifest_path))], "tasks": []}
    if not audit_path.is_file():
        return {"valid": False, "errors": [error("missing_semantic_audit", str(audit_path))], "tasks": []}
    manifest = load_json(manifest_path)
    audit = load_json(audit_path)
    gold = load_json(gold_path)
    gold_tasks = gold.get("tasks", [])
    expected_ids = [task["task_id"] for task in gold_tasks]
    by_gold = {task["task_id"]: task for task in gold_tasks}
    manifest_tasks = manifest.get("tasks", [])
    audit_tasks = audit.get("tasks", [])
    by_manifest = {task.get("task_id"): task for task in manifest_tasks if isinstance(task, dict)}
    by_audit = {task.get("task_id"): task for task in audit_tasks if isinstance(task, dict)}

    prompt_paths = sorted((e4_dir / "prompts").glob("GT*.txt"))
    if len(prompt_paths) != 21:
        errors.append(error("prompt_count", f"expected 21, found {len(prompt_paths)}"))
    prompt_records: dict[str, tuple[Path, str]] = {}
    for path in prompt_paths:
        try:
            task_id, prompt = extract_chinese_prompt(path)
        except ValueError as exc:
            errors.append(error("prompt_format", str(exc)))
            continue
        if task_id in prompt_records:
            errors.append(error("duplicate_task_id", task_id))
        prompt_records[task_id] = (path, prompt)

    if list(prompt_records) != expected_ids:
        errors.append(
            error("task_id_set", f"prompt IDs do not equal canonical order: {list(prompt_records)}")
        )
    if [item.get("task_id") for item in manifest_tasks] != expected_ids:
        errors.append(error("manifest_task_ids", "manifest task IDs/order mismatch"))
    if [item.get("task_id") for item in audit_tasks] != expected_ids:
        errors.append(error("audit_task_ids", "semantic audit task IDs/order mismatch"))

    gold_sha = sha256_file(gold_path)
    if manifest.get("source_gold_sha256") != gold_sha:
        errors.append(error("canonical_gold_sha256_mismatch", "canonical Gold file hash changed"))
    if audit.get("source_gold_sha256") != gold_sha:
        errors.append(error("audit_gold_sha256_mismatch", "audit Gold hash changed"))
    if manifest.get("semantic_contract_fields") != list(SEMANTIC_CONTRACT_FIELDS):
        errors.append(error("semantic_contract_fields", "semantic field list mismatch"))

    sets = manifest.get("condition_prompt_sets", {})
    if set(sets) != {"A", "B", "C"}:
        errors.append(error("condition_prompt_sets", "A/B/C prompt sets required"))
    elif len({entry.get("prompt_source") for entry in sets.values()}) != 1 or len(
        {entry.get("prompt_set_sha256") for entry in sets.values()}
    ) != 1:
        errors.append(error("condition_prompt_hash_mismatch", "A/B/C prompts differ"))

    for task_id in expected_ids:
        row_errors: list[dict[str, str]] = []
        prompt_entry = prompt_records.get(task_id)
        manifest_entry = by_manifest.get(task_id)
        audit_entry = by_audit.get(task_id)
        if prompt_entry is None:
            row_errors.append(error("missing_prompt", task_id))
        if manifest_entry is None:
            row_errors.append(error("missing_manifest_task", task_id))
        if audit_entry is None:
            row_errors.append(error("missing_audit_task", task_id))
        if prompt_entry and manifest_entry:
            path, prompt = prompt_entry
            row_errors.extend(validate_prompt_text(prompt, by_gold[task_id], gold))
            expected_e4_path = str(path.relative_to(root))
            expected_source_path = f"SkillNet_Gold_Tasks_V4/prompts/{task_id}.txt"
            checks = {
                "e4_prompt_path": expected_e4_path,
                "e4_prompt_sha256": sha256_file(path),
                "source_prompt_path": expected_source_path,
                "source_prompt_sha256": sha256_file(root / expected_source_path),
                "source_gold_path": str(gold_path.relative_to(root)),
                "source_gold_sha256": gold_sha,
                "sentence_count": sentence_count(prompt),
                "language": "zh-CN",
                "validation_status": "PASS",
            }
            for field, expected in checks.items():
                if manifest_entry.get(field) != expected:
                    row_errors.append(
                        error("manifest_field_mismatch", f"{field}: {manifest_entry.get(field)!r} != {expected!r}")
                    )
            row_errors.extend(validate_semantic_contract(manifest_entry, by_gold[task_id]))
        if audit_entry:
            row_errors.extend(validate_audit_task(audit_entry))
        task_rows.append(
            {
                "task_id": task_id,
                "status": "PASS" if not row_errors else "FAIL",
                "errors": row_errors,
            }
        )
        errors.extend({"task_id": task_id, **item} for item in row_errors)

    if manifest_tasks:
        actual_set_sha = prompt_set_sha256(manifest_tasks)
        for configuration in ("A", "B", "C"):
            if sets.get(configuration, {}).get("prompt_set_sha256") != actual_set_sha:
                errors.append(
                    error("condition_prompt_hash_mismatch", f"{configuration} prompt set hash mismatch")
                )

    return {
        "schema_version": "1.0",
        "experiment_id": "E4",
        "valid": not errors,
        "prompt_count": len(prompt_records),
        "canonical_gold_sha256": gold_sha,
        "automatic_semantic_equivalence_proven": False,
        "manual_semantic_audit_required": True,
        "tasks": task_rows,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=repository_root())
    args = parser.parse_args()
    report = validate_repository(args.repo)
    print("Task ID | Result | Details")
    print("--- | --- | ---")
    for row in report["tasks"]:
        details = "; ".join(item["code"] for item in row["errors"]) or "all checks passed"
        print(f"{row['task_id']} | {row['status']} | {details}")
    print(
        json.dumps(
            {
                "experiment_id": report["experiment_id"],
                "valid": report["valid"],
                "prompt_count": report["prompt_count"],
                "pass_count": sum(row["status"] == "PASS" for row in report["tasks"]),
                "fail_count": sum(row["status"] == "FAIL" for row in report["tasks"]),
                "automatic_semantic_equivalence_proven": False,
                "manual_semantic_audit_required": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
