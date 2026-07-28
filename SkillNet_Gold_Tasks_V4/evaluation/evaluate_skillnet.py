#!/usr/bin/env python3
"""Deterministic Gold-only evaluator for SkillNet A/B/C routing experiments.

It compares structured Codex predictions only with the self-contained task-level
Gold Standard. It does not read a global relations.json file and does not compute
Graph Validity Rate.

Commands
--------
Validate benchmark consistency:
  python evaluate_skillnet.py validate-package \
    --gold ../02_Gold_Standard_21_V4.json \
    --output ../results/package_validation_report.json

Evaluate one configuration/run:
  python evaluate_skillnet.py evaluate \
    --gold ../02_Gold_Standard_21_V4.json \
    --predictions ../predictions/A/run_01 \
    --configuration A --run-id 1 \
    --output-dir ../results/A_run_01

Aggregate all runs:
  python evaluate_skillnet.py aggregate \
    --input-root ../results \
    --output-dir ../results/summary
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

VALID_STATUS = {"completed", "blocked", "no_tool"}
REQUIRED_FIELDS = {
    "task_id", "use_skills", "selected_departments", "skill_sequence",
    "final_status", "blocked_by", "route_choice", "reason",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_div(num: float, den: float, zero_value: float = 1.0) -> float:
    return num / den if den else zero_value


def precision_recall_f1(predicted: Set[str], gold: Set[str]) -> Tuple[float, float, float]:
    tp = len(predicted & gold)
    precision = safe_div(tp, len(predicted), 1.0 if not gold else 0.0)
    recall = safe_div(tp, len(gold), 1.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def load_predictions(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    files = sorted(p for p in path.rglob("*") if p.suffix.lower() in {".json", ".jsonl"}) if path.is_dir() else [path]
    for file_path in files:
        try:
            if file_path.suffix.lower() == ".jsonl":
                for line_no, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        if not isinstance(obj, dict):
                            raise ValueError("Each JSONL line must be an object")
                        obj["_source_file"] = str(file_path)
                        obj["_source_line"] = line_no
                        records.append(obj)
                    except Exception as exc:
                        records.append({"_parse_error": str(exc), "_raw": line, "_source_file": str(file_path), "_source_line": line_no})
            else:
                obj = load_json(file_path)
                objects = obj if isinstance(obj, list) else [obj]
                for item in objects:
                    if isinstance(item, dict):
                        item["_source_file"] = str(file_path)
                        records.append(item)
                    else:
                        records.append({"_parse_error": "JSON prediction must be an object or list of objects", "_source_file": str(file_path)})
        except Exception as exc:
            records.append({"_parse_error": str(exc), "_source_file": str(file_path)})
    return records


def normalize_name(name: Any, canonical: Set[str], aliases: Dict[str, str]) -> Tuple[Any, bool]:
    if not isinstance(name, str):
        return name, False
    clean = name.strip()
    if clean in canonical:
        return clean, False
    if clean in aliases:
        return aliases[clean], True
    return clean, False


def initial_state(task: Dict[str, Any], skill: str) -> Dict[str, Any]:
    return task.get("initial_skill_states", {}).get(skill, {})


def initially_completed(task: Dict[str, Any], skill: str) -> bool:
    return initial_state(task, skill).get("status") == "completed"


def evaluate_hard_order_pair(task: Dict[str, Any], before: str, after: str, sequence: List[str]) -> Dict[str, Any]:
    positions = {skill: index for index, skill in enumerate(sequence)}
    before_initial = initially_completed(task, before)
    after_initial = initially_completed(task, after)
    before_present = before in positions
    after_present = after in positions

    if after_initial:
        if before_initial:
            return {"satisfied": True, "reason": "both_initially_completed"}
        return {"satisfied": False, "reason": "target_initially_completed_without_required_prior_state"}
    if not after_present:
        return {"satisfied": False, "reason": "missing_after"}
    if before_initial:
        return {"satisfied": True, "reason": "before_initially_completed"}
    if not before_present:
        return {"satisfied": False, "reason": "missing_before"}
    if positions[before] < positions[after]:
        return {"satisfied": True, "reason": "correct_order"}
    return {"satisfied": False, "reason": "reversed_order"}


def hard_order_results(task: Dict[str, Any], sequence: List[str]) -> List[Dict[str, Any]]:
    results = []
    for pair in task.get("hard_order_constraints", []):
        results.append({
            "before": pair["before"],
            "after": pair["after"],
            "constraint_type": pair.get("constraint_type", "mandatory_order"),
            **evaluate_hard_order_pair(task, pair["before"], pair["after"], sequence),
        })
    return results


def task_constraint_violations(task: Dict[str, Any], sequence: List[str], route_choice: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    conflict_violations: List[Dict[str, Any]] = []
    mutex_violations: List[Dict[str, Any]] = []
    selected = set(sequence)
    states = task.get("initial_skill_states", {})

    for rule in task.get("task_constraints", []):
        if rule.get("type") == "conflict_block":
            trigger = rule["trigger_skill"]
            state = states.get(trigger, {})
            if state.get("status") == "completed" and state.get("result") in set(rule.get("trigger_results", [])):
                hits = sorted(selected & set(rule.get("blocked_skills", [])))
                if hits:
                    conflict_violations.append({"trigger_skill": trigger, "trigger_result": state.get("result"), "blocked_skills_called": hits})
        elif rule.get("type") == "mutex_route":
            decision_id = rule["decision_id"]
            expected = rule["expected_choice"]
            actual = route_choice.get(decision_id)
            forbidden_hits = sorted(selected & set(rule.get("forbidden_route_skills", [])))
            if actual is not None and actual != expected:
                mutex_violations.append({"decision_id": decision_id, "expected_choice": expected, "actual_choice": actual, "type": "wrong_route_choice"})
            if forbidden_hits:
                mutex_violations.append({"decision_id": decision_id, "expected_choice": expected, "forbidden_route_skills_called": forbidden_hits, "type": "forbidden_route_skill"})
    return conflict_violations, mutex_violations


def validate_package(gold: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    skills = set(gold.get("skill_catalog", {}))
    departments = set(gold.get("department_catalog", []))

    if len(skills) != 46:
        errors.append({"scope": "gold", "error": "atomic_skill_count_mismatch", "actual": len(skills), "expected": 46})
    if len(departments) != 5:
        errors.append({"scope": "gold", "error": "department_count_mismatch", "actual": len(departments), "expected": 5})
    if gold.get("task_count") != len(gold.get("tasks", [])):
        errors.append({"scope": "gold", "error": "task_count_mismatch"})

    seen: Set[str] = set()
    for task in gold.get("tasks", []):
        tid = task.get("task_id")
        if tid in seen:
            errors.append({"task_id": tid, "error": "duplicate_task_id"})
        seen.add(tid)
        if task.get("expected_final_status") not in VALID_STATUS:
            errors.append({"task_id": tid, "error": "invalid_expected_final_status"})

        for field in ("required_skills", "optional_skills", "forbidden_skills"):
            for skill in task.get(field, []):
                if skill != "ALL_BUSINESS_SKILLS" and skill not in skills:
                    errors.append({"task_id": tid, "error": "unknown_gold_skill", "field": field, "skill": skill})
        for skill in task.get("initial_skill_states", {}):
            if skill not in skills:
                errors.append({"task_id": tid, "error": "unknown_initial_state_skill", "skill": skill})
        for dep in task.get("required_departments", []):
            if dep not in departments:
                errors.append({"task_id": tid, "error": "unknown_gold_department", "department": dep})

        required = set(task.get("required_skills", []))
        optional = set(task.get("optional_skills", []))
        forbidden = set(task.get("forbidden_skills", []))
        initial = set(task.get("initial_skill_states", {}))
        if required & forbidden:
            errors.append({"task_id": tid, "error": "required_and_forbidden_overlap", "skills": sorted(required & forbidden)})
        if optional & forbidden:
            errors.append({"task_id": tid, "error": "optional_and_forbidden_overlap", "skills": sorted(optional & forbidden)})
        if required & initial:
            errors.append({"task_id": tid, "error": "required_skill_already_in_initial_state", "skills": sorted(required & initial)})

        implied_departments = {gold["skill_catalog"][s] for s in required if s in skills}
        missing_dep_labels = implied_departments - set(task.get("required_departments", []))
        if missing_dep_labels:
            errors.append({"task_id": tid, "error": "required_skill_department_missing", "departments": sorted(missing_dep_labels)})

        canonical = task.get("canonical_sequence", [])
        if task.get("expected_final_status") == "completed" and set(canonical) != required:
            warnings.append({"task_id": tid, "warning": "canonical_sequence_not_equal_required_skill_set", "difference": sorted(set(canonical) ^ required)})

        for pair in task.get("hard_order_constraints", []):
            before, after = pair.get("before"), pair.get("after")
            if before not in required and before not in initial:
                errors.append({"task_id": tid, "error": "hard_before_not_required_or_initial", "skill": before})
            if after not in required and after not in initial:
                errors.append({"task_id": tid, "error": "hard_after_not_required_or_initial", "skill": after})

        for rule in task.get("task_constraints", []):
            if rule.get("type") == "conflict_block":
                trigger = rule.get("trigger_skill")
                if trigger not in skills:
                    errors.append({"task_id": tid, "error": "unknown_conflict_trigger", "skill": trigger})
                for skill in rule.get("blocked_skills", []):
                    if skill not in skills:
                        errors.append({"task_id": tid, "error": "unknown_conflict_blocked_skill", "skill": skill})
                state = task.get("initial_skill_states", {}).get(trigger, {})
                if state.get("status") != "completed" or state.get("result") not in set(rule.get("trigger_results", [])):
                    errors.append({"task_id": tid, "error": "conflict_trigger_not_active_in_initial_state", "skill": trigger})
            elif rule.get("type") == "mutex_route":
                decision_id = rule.get("decision_id")
                expected = rule.get("expected_choice")
                if task.get("expected_route_choice", {}).get(decision_id) != expected:
                    errors.append({"task_id": tid, "error": "mutex_expected_route_mismatch", "decision_id": decision_id})
                for skill in rule.get("forbidden_route_skills", []):
                    if skill not in skills:
                        errors.append({"task_id": tid, "error": "unknown_mutex_forbidden_skill", "skill": skill})

    return {"valid": not errors, "task_count": len(gold.get("tasks", [])), "skill_count": len(skills), "errors": errors, "warnings": warnings}


def evaluate_record(prediction: Dict[str, Any], task: Dict[str, Any], gold: Dict[str, Any], configuration: str, run_id: str) -> Dict[str, Any]:
    hard_failures: List[str] = []
    soft_failures: List[str] = []
    format_valid = True

    if "_parse_error" in prediction:
        format_valid = False
        hard_failures.append("FORMAT_INVALID_JSON")
    missing_fields = sorted(REQUIRED_FIELDS - set(prediction)) if format_valid else sorted(REQUIRED_FIELDS)
    if missing_fields:
        format_valid = False
        hard_failures.append("FORMAT_MISSING_FIELD")

    canonical_skills = set(gold["skill_catalog"])
    canonical_departments = set(gold["department_catalog"])
    aliases = gold.get("aliases", {})

    use_skills = prediction.get("use_skills") if isinstance(prediction.get("use_skills"), bool) else None
    final_status = prediction.get("final_status") if prediction.get("final_status") in VALID_STATUS else None
    if prediction.get("final_status") not in VALID_STATUS:
        format_valid = False
        hard_failures.append("FORMAT_INVALID_VALUE")

    raw_sequence = prediction.get("skill_sequence") if isinstance(prediction.get("skill_sequence"), list) else []
    raw_departments = prediction.get("selected_departments") if isinstance(prediction.get("selected_departments"), list) else []
    blocked_by_raw = prediction.get("blocked_by") if isinstance(prediction.get("blocked_by"), list) else []
    route_choice = prediction.get("route_choice") if isinstance(prediction.get("route_choice"), dict) else {}
    if not isinstance(prediction.get("skill_sequence"), list) or not isinstance(prediction.get("selected_departments"), list) or not isinstance(prediction.get("blocked_by"), list) or not isinstance(prediction.get("route_choice"), dict):
        format_valid = False
        hard_failures.append("FORMAT_INVALID_VALUE")

    sequence: List[str] = []
    predicted_departments: List[str] = []
    blocked_by: List[str] = []
    aliases_used: List[Dict[str, str]] = []
    for value in raw_sequence:
        normalized, used = normalize_name(value, canonical_skills, aliases)
        sequence.append(normalized)
        if used:
            aliases_used.append({"input": value, "canonical": normalized})
    for value in raw_departments:
        normalized, used = normalize_name(value, canonical_departments, aliases)
        predicted_departments.append(normalized)
        if used:
            aliases_used.append({"input": value, "canonical": normalized})
    for value in blocked_by_raw:
        normalized, used = normalize_name(value, canonical_skills, aliases)
        blocked_by.append(normalized)
        if used:
            aliases_used.append({"input": value, "canonical": normalized})

    unknown_skills = sorted({s for s in sequence if s not in canonical_skills})
    unknown_departments = sorted({d for d in predicted_departments if d not in canonical_departments})
    duplicate_skills = sorted({s for s in sequence if sequence.count(s) > 1})
    repeated_initial_skills = sorted({s for s in sequence if initially_completed(task, s)})

    required_skills = set(task.get("required_skills", []))
    optional_skills = set(task.get("optional_skills", []))
    acceptable_skills = required_skills | optional_skills
    predicted_known_skills = {s for s in sequence if s in canonical_skills}
    missing_required_skills = sorted(required_skills - predicted_known_skills)
    extra_skills = sorted(predicted_known_skills - acceptable_skills)
    skill_precision, skill_recall, skill_f1 = precision_recall_f1(predicted_known_skills, required_skills)
    # Optional skills are accepted for precision.
    if predicted_known_skills:
        skill_precision = len(predicted_known_skills & acceptable_skills) / len(predicted_known_skills)
        skill_f1 = 2 * skill_precision * skill_recall / (skill_precision + skill_recall) if skill_precision + skill_recall else 0.0

    gold_departments = set(task.get("required_departments", []))
    predicted_known_departments = {d for d in predicted_departments if d in canonical_departments}
    department_precision, department_recall, department_f1 = precision_recall_f1(predicted_known_departments, gold_departments)
    missing_departments = sorted(gold_departments - predicted_known_departments)
    extra_departments = sorted(predicted_known_departments - gold_departments)

    order_results = hard_order_results(task, sequence)
    unsatisfied_order_pairs = [r for r in order_results if not r["satisfied"]]
    required_order_accuracy = safe_div(len(order_results) - len(unsatisfied_order_pairs), len(order_results), 1.0)

    forbidden = set(task.get("forbidden_skills", []))
    forbidden_hits = sorted(predicted_known_skills & forbidden)
    conflict_v, mutex_v = task_constraint_violations(task, sequence, route_choice)

    expected_blockers = set(task.get("expected_blocked_by", []))
    blocker_precision, blocker_recall, blocker_f1 = precision_recall_f1(set(blocked_by), expected_blockers)
    expected_route_choice = task.get("expected_route_choice", {})
    route_choice_correct = all(route_choice.get(k) == v for k, v in expected_route_choice.items())
    use_skills_correct = use_skills == bool(task.get("use_skills"))
    final_status_correct = final_status == task.get("expected_final_status")

    if not use_skills_correct:
        hard_failures.append("FALSE_TOOL_ACTIVATION" if not task.get("use_skills") else "FALSE_ABSTENTION")
    if unknown_skills:
        hard_failures.append("UNKNOWN_SKILL")
    if unknown_departments:
        hard_failures.append("UNKNOWN_DEPARTMENT")
    if missing_required_skills:
        hard_failures.append("MISSING_REQUIRED_SKILL")
    if extra_skills:
        soft_failures.append("UNNECESSARY_SKILL")
    if unsatisfied_order_pairs:
        hard_failures.append("ORDER_VIOLATION")
    if forbidden_hits:
        hard_failures.append("FORBIDDEN_SKILL_VIOLATION")
    if conflict_v:
        hard_failures.append("CONFLICT_VIOLATION")
    if mutex_v:
        hard_failures.append("MUTEX_VIOLATION")
    if missing_departments:
        hard_failures.append("MISSING_DEPARTMENT")
    if extra_departments:
        soft_failures.append("EXTRA_DEPARTMENT")
    if duplicate_skills:
        soft_failures.append("DUPLICATE_SKILL")
    if repeated_initial_skills:
        hard_failures.append("REPEATED_COMPLETED_SKILL")
    if not final_status_correct:
        hard_failures.append("WRONG_FINAL_STATUS")
    if task.get("expected_final_status") == "blocked" and expected_blockers and blocker_recall < 1.0:
        hard_failures.append("WRONG_BLOCK_REASON")
    if not route_choice_correct:
        hard_failures.append("WRONG_ROUTE_CHOICE")
    if task.get("expected_final_status") == "blocked" and (forbidden_hits or conflict_v):
        hard_failures.append("CONTINUE_AFTER_BLOCK")

    gold_constraint_violated = bool(
        unsatisfied_order_pairs or forbidden_hits or conflict_v or mutex_v or
        repeated_initial_skills or not route_choice_correct or
        (task.get("expected_final_status") == "blocked" and expected_blockers and blocker_recall < 1.0)
    )

    expected_status = task.get("expected_final_status")
    no_tool_correct = (
        expected_status == "no_tool" and format_valid and use_skills is False and
        final_status == "no_tool" and not sequence and not predicted_departments
    )
    blocked_flow_correct = (
        expected_status == "blocked" and format_valid and use_skills_correct and
        final_status_correct and blocker_recall == 1.0 and not forbidden_hits and
        not conflict_v and not mutex_v and not unknown_skills and department_recall == 1.0
    )

    if expected_status == "no_tool":
        functional_success = no_tool_correct
    elif expected_status == "blocked":
        functional_success = blocked_flow_correct and route_choice_correct
    else:
        functional_success = all([
            format_valid, use_skills_correct, final_status_correct,
            skill_recall == 1.0, required_order_accuracy == 1.0,
            department_recall == 1.0, not gold_constraint_violated,
            not unknown_skills, route_choice_correct,
        ])

    clean_success = all([
        functional_success, skill_precision == 1.0,
        department_precision == 1.0, not duplicate_skills,
    ])

    priority = [
        "FORMAT_INVALID_JSON", "FORMAT_MISSING_FIELD", "FORMAT_INVALID_VALUE",
        "FALSE_TOOL_ACTIVATION", "FALSE_ABSTENTION", "WRONG_FINAL_STATUS",
        "WRONG_BLOCK_REASON", "WRONG_ROUTE_CHOICE", "CONFLICT_VIOLATION",
        "MUTEX_VIOLATION", "FORBIDDEN_SKILL_VIOLATION", "CONTINUE_AFTER_BLOCK",
        "REPEATED_COMPLETED_SKILL", "MISSING_REQUIRED_SKILL", "ORDER_VIOLATION",
        "UNKNOWN_SKILL", "UNKNOWN_DEPARTMENT", "MISSING_DEPARTMENT",
    ]
    all_tags = list(dict.fromkeys(hard_failures + soft_failures))
    primary_failure = next((tag for tag in priority if tag in all_tags), None)
    secondary_failures = [tag for tag in all_tags if tag != primary_failure]

    return {
        "configuration": configuration,
        "run_id": run_id,
        "task_id": task["task_id"],
        "category": task["category"],
        "difficulty": task["difficulty"],
        "format_valid": format_valid,
        "functional_success": functional_success,
        "clean_success": clean_success,
        "use_skills_correct": use_skills_correct,
        "final_status_correct": final_status_correct,
        "no_tool_correct": no_tool_correct if expected_status == "no_tool" else "",
        "blocked_flow_correct": blocked_flow_correct if expected_status == "blocked" else "",
        "skill_precision": round(skill_precision, 6),
        "skill_recall": round(skill_recall, 6),
        "skill_f1": round(skill_f1, 6),
        "department_precision": round(department_precision, 6),
        "department_recall": round(department_recall, 6),
        "department_f1": round(department_f1, 6),
        "required_order_accuracy": round(required_order_accuracy, 6),
        "gold_constraint_violated": gold_constraint_violated,
        "blocked_reason_f1": round(blocker_f1, 6),
        "route_choice_correct": route_choice_correct,
        "predicted_skill_count": len(sequence),
        "required_skill_count": len(required_skills),
        "unnecessary_skill_count": len(extra_skills),
        "unknown_skills": unknown_skills,
        "unknown_departments": unknown_departments,
        "missing_required_skills": missing_required_skills,
        "extra_skills": extra_skills,
        "hard_order_results": order_results,
        "unsatisfied_order_pairs": unsatisfied_order_pairs,
        "forbidden_hits": forbidden_hits,
        "conflict_violations": conflict_v,
        "mutex_violations": mutex_v,
        "missing_departments": missing_departments,
        "extra_departments": extra_departments,
        "duplicate_skills": duplicate_skills,
        "repeated_initial_skills": repeated_initial_skills,
        "aliases_used": aliases_used,
        "primary_failure": primary_failure,
        "secondary_failures": secondary_failures,
        "model_reason": prediction.get("reason", ""),
        "source_file": prediction.get("_source_file", ""),
        "source_line": prediction.get("_source_line", ""),
    }


def flatten_for_csv(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()}


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(flatten_for_csv(r) for r in rows)


def summarize(rows: List[Dict[str, Any]], group_keys: List[str]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in group_keys)].append(row)
    metrics = [
        "functional_success", "clean_success", "skill_precision", "skill_recall",
        "skill_f1", "department_f1", "required_order_accuracy",
        "final_status_correct", "route_choice_correct",
    ]
    output = []
    for group, items in sorted(groups.items()):
        record = {k: v for k, v in zip(group_keys, group)}
        record["n"] = len(items)
        for metric in metrics:
            record[metric] = round(sum(float(bool(i[metric])) if isinstance(i[metric], bool) else float(i[metric]) for i in items) / len(items), 6)
        record["gold_constraint_violation_rate"] = round(sum(bool(i["gold_constraint_violated"]) for i in items) / len(items), 6)
        output.append(record)
    return output


def command_validate_package(args: argparse.Namespace) -> None:
    report = validate_package(load_json(Path(args.gold)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(2)


def command_evaluate(args: argparse.Namespace) -> None:
    gold = load_json(Path(args.gold))
    tasks = {t["task_id"]: t for t in gold["tasks"]}
    predictions = load_predictions(Path(args.predictions))
    predictions_by_task: Dict[str, Dict[str, Any]] = {}
    unmatched: List[Dict[str, Any]] = []
    duplicates: List[Dict[str, Any]] = []
    for prediction in predictions:
        tid = prediction.get("task_id")
        if tid in tasks:
            if tid in predictions_by_task:
                duplicates.append(prediction)
            else:
                predictions_by_task[tid] = prediction
        else:
            unmatched.append(prediction)

    rows = []
    for tid, task in tasks.items():
        prediction = predictions_by_task.get(tid, {"task_id": tid, "_parse_error": "missing prediction"})
        rows.append(evaluate_record(prediction, task, gold, args.configuration, str(args.run_id)))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "per_task_results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(output_dir / "per_task_results.csv", rows)
    write_csv(output_dir / "summary_by_configuration.csv", summarize(rows, ["configuration", "run_id"]))
    write_csv(output_dir / "summary_by_category.csv", summarize(rows, ["configuration", "run_id", "category"]))

    failure_counter: Counter[Tuple[str, str]] = Counter()
    for row in rows:
        if row["primary_failure"]:
            failure_counter[(row["configuration"], row["primary_failure"])] += 1
        for failure in row["secondary_failures"]:
            failure_counter[(row["configuration"], failure)] += 1
    write_csv(output_dir / "failure_analysis.csv", [
        {"configuration": c, "failure_type": f, "count": n, "rate": round(n / len(rows), 6)}
        for (c, f), n in sorted(failure_counter.items())
    ])

    manual_review = [
        {"configuration": r["configuration"], "run_id": r["run_id"], "task_id": r["task_id"],
         "primary_failure": r["primary_failure"], "secondary_failures": r["secondary_failures"],
         "aliases_used": r["aliases_used"], "model_reason": r["model_reason"], "source_file": r["source_file"]}
        for r in rows if r["primary_failure"] or r["aliases_used"]
    ]
    write_csv(output_dir / "manual_review_queue.csv", manual_review)
    (output_dir / "unmatched_or_duplicate_predictions.json").write_text(json.dumps({"unmatched": unmatched, "duplicates": duplicates}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"evaluated_tasks": len(rows), "output_dir": str(output_dir), "unmatched_prediction_records": len(unmatched), "duplicate_prediction_records": len(duplicates)}, ensure_ascii=False, indent=2))


def command_aggregate(args: argparse.Namespace) -> None:
    root = Path(args.input_root)
    result_files = sorted(root.rglob("per_task_results.json"))
    rows: List[Dict[str, Any]] = []
    for file in result_files:
        rows.extend(load_json(file))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "all_per_task_results.csv", rows)
    write_csv(output_dir / "summary_by_configuration.csv", summarize(rows, ["configuration"]))
    write_csv(output_dir / "summary_by_configuration_and_category.csv", summarize(rows, ["configuration", "category"]))

    scores: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for row in rows:
        scores[(row["task_id"], row["configuration"])].append(float(row["functional_success"]))
    configs = sorted({row["configuration"] for row in rows})
    task_ids = sorted({row["task_id"] for row in rows})
    pairwise = []
    for tid in task_ids:
        record: Dict[str, Any] = {"task_id": tid}
        for config in configs:
            vals = scores.get((tid, config), [])
            record[config] = round(sum(vals) / len(vals), 6) if vals else ""
        pairwise.append(record)
    write_csv(output_dir / "pairwise_comparison.csv", pairwise)

    failure_counter: Counter[Tuple[str, str]] = Counter()
    denominators = Counter(row["configuration"] for row in rows)
    for row in rows:
        if row.get("primary_failure"):
            failure_counter[(row["configuration"], row["primary_failure"])] += 1
        for failure in row.get("secondary_failures", []):
            failure_counter[(row["configuration"], failure)] += 1
    write_csv(output_dir / "failure_analysis.csv", [
        {"configuration": c, "failure_type": f, "count": n, "rate": round(n / denominators[c], 6)}
        for (c, f), n in sorted(failure_counter.items())
    ])
    print(json.dumps({"input_result_files": len(result_files), "rows": len(rows), "output_dir": str(output_dir)}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate-package")
    p.add_argument("--gold", required=True)
    p.add_argument("--output", required=True)
    p.set_defaults(func=command_validate_package)
    p = sub.add_parser("evaluate")
    p.add_argument("--gold", required=True)
    p.add_argument("--predictions", required=True)
    p.add_argument("--configuration", required=True)
    p.add_argument("--run-id", default="1")
    p.add_argument("--output-dir", required=True)
    p.set_defaults(func=command_evaluate)
    p = sub.add_parser("aggregate")
    p.add_argument("--input-root", required=True)
    p.add_argument("--output-dir", required=True)
    p.set_defaults(func=command_aggregate)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
