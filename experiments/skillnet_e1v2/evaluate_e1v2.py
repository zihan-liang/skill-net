#!/usr/bin/env python3
"""Deterministic metric-split evaluator for frozen SkillNet E1-v2.

The unchanged canonical evaluator remains authoritative for E0/E1. This
isolated evaluator implements E1-v2 strict, semantic, routing, and control
metrics without changing old result semantics.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLD = (
    ROOT / "SkillNet_Gold_Tasks_V4" / "e1v2" / "E1V2_Gold_21.json"
)
DEFAULT_SCHEMA = Path(__file__).resolve().parent / "prediction_schema_e1v2.json"
DEFAULT_NORMALIZATION = (
    Path(__file__).resolve().parent / "semantic_normalization.json"
)
VALID_STATUS = {"completed", "blocked", "no_tool"}
REQUIRED_FIELDS = {
    "task_id",
    "use_skills",
    "selected_departments",
    "skill_sequence",
    "final_status",
    "blocked_by",
    "route_choice",
    "reason",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_div(
    numerator: float, denominator: float, zero_value: float = 1.0
) -> float:
    return numerator / denominator if denominator else zero_value


def precision_recall_f1(
    predicted: set[str], gold: set[str]
) -> tuple[float, float, float]:
    true_positive = len(predicted & gold)
    precision = safe_div(
        true_positive, len(predicted), 1.0 if not gold else 0.0
    )
    recall = safe_div(true_positive, len(gold), 1.0)
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return precision, recall, f1


def initially_completed(task: dict[str, Any], skill: str) -> bool:
    return (
        task.get("initial_skill_states", {})
        .get(skill, {})
        .get("status")
        == "completed"
    )


def hard_order_results(
    task: dict[str, Any], sequence: list[str]
) -> list[dict[str, Any]]:
    positions = {skill: index for index, skill in enumerate(sequence)}
    output = []
    for pair in task.get("hard_order_constraints", []):
        before, after = pair["before"], pair["after"]
        before_initial = initially_completed(task, before)
        after_initial = initially_completed(task, after)
        if after_initial:
            satisfied = before_initial
            reason = (
                "both_initially_completed"
                if satisfied
                else "target_initially_completed_without_required_prior_state"
            )
        elif after not in positions:
            satisfied, reason = False, "missing_after"
        elif before_initial:
            satisfied, reason = True, "before_initially_completed"
        elif before not in positions:
            satisfied, reason = False, "missing_before"
        elif positions[before] < positions[after]:
            satisfied, reason = True, "correct_order"
        else:
            satisfied, reason = False, "reversed_order"
        output.append(
            {
                "before": before,
                "after": after,
                "constraint_type": pair.get(
                    "constraint_type", "mandatory_order"
                ),
                "satisfied": satisfied,
                "reason": reason,
            }
        )
    return output


def validate_prediction(
    prediction: Any,
    *,
    schema_valid: bool | None,
    expected_task_id: str,
) -> tuple[bool, list[str]]:
    if not isinstance(prediction, dict) or "_parse_error" in prediction:
        return False, [
            (
                str(prediction.get("_parse_error"))
                if isinstance(prediction, dict)
                else "prediction_not_object"
            )
        ]
    if schema_valid is False:
        return False, ["upstream_schema_invalid"]
    schema = load_json(DEFAULT_SCHEMA)
    errors = [
        error.message
        for error in Draft202012Validator(schema).iter_errors(prediction)
    ]
    if prediction.get("task_id") != expected_task_id:
        errors.append(
            f"task_id must equal {expected_task_id!r}"
        )
    return not errors, errors


def normalize_route_choice(
    route_choice: dict[str, Any],
    rules: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    normalized = {}
    applied = []
    key_aliases = rules["route_key_aliases"]
    value_aliases = rules["route_value_aliases"]
    for raw_key, raw_value in route_choice.items():
        key = key_aliases.get(raw_key, raw_key)
        value = value_aliases.get(raw_value, raw_value)
        if key != raw_key:
            applied.append(
                {
                    "type": "key_alias",
                    "input": raw_key,
                    "output": key,
                }
            )
        if value != raw_value:
            applied.append(
                {
                    "type": "value_alias",
                    "input": str(raw_value),
                    "output": str(value),
                }
            )
        normalized[key] = value
    return normalized, applied


def harmless_no_tool_route(
    route_choice: dict[str, Any], rules: dict[str, Any]
) -> bool:
    if not route_choice:
        return True
    policy = rules["no_tool_harmless_redundancy"]
    if not set(route_choice) <= set(policy["allowed_keys"]):
        return False
    values = list(route_choice.values())
    return (
        all(isinstance(value, str) for value in values)
        and set(values) <= set(policy["allowed_values"])
        and policy["must_contain_value"] in values
    )


def semantic_route_choice(
    task: dict[str, Any],
    sequence: list[str],
    route_choice: dict[str, Any],
    rules: dict[str, Any],
) -> dict[str, Any]:
    expected = task.get("expected_route_choice", {})
    normalized, applied = normalize_route_choice(route_choice, rules)
    if task.get("expected_final_status") == "no_tool":
        correct = harmless_no_tool_route(route_choice, rules)
        return {
            "correct": correct,
            "expected": {},
            "normalized_route_choice": normalized,
            "normalization_rules_applied": applied,
            "judgment_source": "no_tool_harmless_redundancy_policy",
            "sequence_evidence": {},
        }
    if not expected:
        return {
            "correct": True,
            "expected": {},
            "normalized_route_choice": normalized,
            "normalization_rules_applied": applied,
            "judgment_source": "no_route_decision_in_gold",
            "sequence_evidence": {},
        }

    sequence_set = set(sequence)
    judgments = []
    for decision_id, expected_choice in expected.items():
        domain = rules["route_domains"].get(decision_id, {})
        expected_policy = domain.get(expected_choice)
        if not expected_policy:
            judgments.append(
                {
                    "decision_id": decision_id,
                    "expected_choice": expected_choice,
                    "correct": False,
                    "source": "unfrozen_expected_route",
                }
            )
            continue
        expected_positive = set(expected_policy["positive_sequence_skills"])
        expected_forbidden = set(expected_policy["forbidden_sequence_skills"])
        expected_hits = sorted(sequence_set & expected_positive)
        forbidden_hits = sorted(sequence_set & expected_forbidden)
        mode = expected_policy["positive_evidence_mode"]
        sufficient = (
            bool(expected_hits)
            if mode == "any"
            else expected_positive <= sequence_set
        )
        if forbidden_hits:
            correct, source = False, "conflicting_sequence_evidence"
        elif sufficient:
            correct, source = True, "skill_sequence"
        else:
            correct = normalized.get(decision_id) == expected_choice
            source = "normalized_route_choice_fallback"
        judgments.append(
            {
                "decision_id": decision_id,
                "expected_choice": expected_choice,
                "normalized_choice": normalized.get(decision_id),
                "positive_hits": expected_hits,
                "forbidden_hits": forbidden_hits,
                "positive_evidence_mode": mode,
                "correct": correct,
                "source": source,
            }
        )
    return {
        "correct": all(item["correct"] for item in judgments),
        "expected": expected,
        "normalized_route_choice": normalized,
        "normalization_rules_applied": applied,
        "judgment_source": "sequence_first_then_normalized_fallback",
        "sequence_evidence": judgments,
    }


def constraint_violations(
    task: dict[str, Any],
    sequence: list[str],
    *,
    semantic_route_correct: bool,
    strict_route_correct: bool,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    selected = set(sequence)
    states = task.get("initial_skill_states", {})
    conflicts = []
    strict_mutex = []
    semantic_mutex = []
    for rule in task.get("task_constraints", []):
        if rule.get("type") == "conflict_block":
            trigger = rule["trigger_skill"]
            state = states.get(trigger, {})
            active = (
                state.get("status") == "completed"
                and state.get("result")
                in set(rule.get("trigger_results", []))
            )
            hits = sorted(selected & set(rule.get("blocked_skills", [])))
            if active and hits:
                conflicts.append(
                    {
                        "trigger_skill": trigger,
                        "trigger_result": state.get("result"),
                        "blocked_skills_called": hits,
                    }
                )
        elif rule.get("type") == "mutex_route":
            hits = sorted(
                selected & set(rule.get("forbidden_route_skills", []))
            )
            if hits:
                violation = {
                    "decision_id": rule["decision_id"],
                    "expected_choice": rule["expected_choice"],
                    "forbidden_route_skills_called": hits,
                    "type": "forbidden_route_skill",
                }
                strict_mutex.append(violation)
                semantic_mutex.append(violation)
            if not strict_route_correct:
                strict_mutex.append(
                    {
                        "decision_id": rule["decision_id"],
                        "expected_choice": rule["expected_choice"],
                        "type": "strict_route_mismatch",
                    }
                )
            if not semantic_route_correct:
                semantic_mutex.append(
                    {
                        "decision_id": rule["decision_id"],
                        "expected_choice": rule["expected_choice"],
                        "type": "semantic_route_mismatch",
                    }
                )
    return conflicts, strict_mutex, semantic_mutex


def empty_failure_row(
    task: dict[str, Any],
    configuration: str,
    run_id: str,
    *,
    transport_failure: bool,
    format_errors: list[str],
) -> dict[str, Any]:
    expected_status = task.get("expected_final_status")
    return {
        "configuration": configuration,
        "run_id": run_id,
        "task_id": task["task_id"],
        "category": task["category"],
        "difficulty": task["difficulty"],
        "format_valid": False,
        "format_errors": format_errors,
        "strict_functional_success": False,
        "semantic_functional_success": False,
        "skill_routing_success": False,
        "control_success": False,
        "use_skills_correct": False,
        "final_status_correct": False,
        "no_tool_correct": False if expected_status == "no_tool" else "",
        "blocked_flow_correct": False if expected_status == "blocked" else "",
        "skill_precision": 0.0,
        "skill_recall": 0.0,
        "skill_f1": 0.0,
        "department_precision": 0.0,
        "department_recall": 0.0,
        "department_f1": 0.0,
        "required_order_accuracy": 0.0,
        "strict_route_choice_correct": False,
        "semantic_route_choice_correct": False,
        "blocked_reason_f1": 0.0,
        "strict_gold_constraint_violated": True,
        "semantic_gold_constraint_violated": True,
        "missing_required_skills": list(task.get("required_skills", [])),
        "extra_skills": [],
        "unknown_skills": [],
        "unknown_departments": [],
        "duplicate_skills": [],
        "repeated_initial_skills": [],
        "forbidden_hits": [],
        "unsatisfied_order_pairs": list(
            task.get("hard_order_constraints", [])
        ),
        "conflict_violations": [],
        "strict_mutex_violations": [],
        "semantic_mutex_violations": [],
        "missing_departments": list(task.get("required_departments", [])),
        "extra_departments": [],
        "missing_required_skill_count": len(
            task.get("required_skills", [])
        ),
        "extra_skill_count": 0,
        "forbidden_skill_count": 0,
        "repeated_completed_skill_count": 0,
        "unsatisfied_order_pair_count": len(
            task.get("hard_order_constraints", [])
        ),
        "conflict_violation_count": 0,
        "mutex_violation_count": 0,
        "continue_after_block_count": 0,
        "transport_failure_count": int(transport_failure),
        "semantic_route_judgment": {},
        "semantic_expression_audit": None,
        "model_reason": "",
    }


def evaluate_record(
    prediction: dict[str, Any] | None,
    task: dict[str, Any],
    gold: dict[str, Any],
    configuration: str,
    run_id: str,
    *,
    transport_failure: bool = False,
    schema_valid: bool | None = None,
) -> dict[str, Any]:
    format_valid, format_errors = validate_prediction(
        prediction,
        schema_valid=schema_valid,
        expected_task_id=task["task_id"],
    )
    if transport_failure or not format_valid or prediction is None:
        return empty_failure_row(
            task,
            configuration,
            run_id,
            transport_failure=transport_failure,
            format_errors=format_errors,
        )

    canonical_skills = set(gold["skill_catalog"])
    canonical_departments = set(gold["department_catalog"])
    sequence = list(prediction["skill_sequence"])
    departments = list(prediction["selected_departments"])
    blocked_by = list(prediction["blocked_by"])
    route_choice = dict(prediction["route_choice"])
    use_skills = prediction["use_skills"]
    final_status = prediction["final_status"]
    rules = load_json(DEFAULT_NORMALIZATION)

    unknown_skills = sorted(
        {
            value
            for value in [*sequence, *blocked_by]
            if value not in canonical_skills
        }
    )
    unknown_departments = sorted(
        {
            value
            for value in departments
            if value not in canonical_departments
        }
    )
    duplicate_skills = sorted(
        {
            skill
            for skill in sequence
            if sequence.count(skill) > 1
        }
    )
    repeated_initial = sorted(
        {skill for skill in sequence if initially_completed(task, skill)}
    )
    known_sequence = {skill for skill in sequence if skill in canonical_skills}
    required = set(task.get("required_skills", []))
    optional = set(task.get("optional_skills", []))
    acceptable = required | optional
    missing_required = sorted(required - known_sequence)
    extra_skills = sorted(known_sequence - acceptable)
    skill_precision, skill_recall, skill_f1 = precision_recall_f1(
        known_sequence, required
    )
    if known_sequence:
        skill_precision = len(known_sequence & acceptable) / len(known_sequence)
        skill_f1 = (
            2 * skill_precision * skill_recall
            / (skill_precision + skill_recall)
            if skill_precision + skill_recall
            else 0.0
        )

    known_departments = {
        department
        for department in departments
        if department in canonical_departments
    }
    required_departments = set(task.get("required_departments", []))
    department_precision, department_recall, department_f1 = (
        precision_recall_f1(known_departments, required_departments)
    )
    missing_departments = sorted(required_departments - known_departments)
    extra_departments = sorted(known_departments - required_departments)

    orders = hard_order_results(task, sequence)
    unsatisfied_orders = [item for item in orders if not item["satisfied"]]
    order_accuracy = safe_div(
        len(orders) - len(unsatisfied_orders), len(orders), 1.0
    )
    forbidden = (
        set(canonical_skills)
        if task.get("forbid_all_skills", False)
        else set(task.get("forbidden_skills", []))
    )
    forbidden_hits = sorted(known_sequence & forbidden)

    expected_route = task.get("expected_route_choice", {})
    strict_route_correct = route_choice == expected_route
    semantic_route = semantic_route_choice(
        task, sequence, route_choice, rules
    )
    semantic_route_correct = semantic_route["correct"]
    conflicts, strict_mutex, semantic_mutex = constraint_violations(
        task,
        sequence,
        semantic_route_correct=semantic_route_correct,
        strict_route_correct=strict_route_correct,
    )

    expected_blockers = set(task.get("expected_blocked_by", []))
    blocker_precision, blocker_recall, blocker_f1 = precision_recall_f1(
        set(blocked_by), expected_blockers
    )
    exact_blockers = set(blocked_by) == expected_blockers and (
        len(blocked_by) == len(set(blocked_by))
    )
    use_skills_correct = use_skills == bool(task.get("use_skills"))
    final_status_correct = final_status == task.get("expected_final_status")
    expected_status = task.get("expected_final_status")
    continue_after_block = int(
        expected_status == "blocked" and bool(sequence)
    )

    strict_gold_violated = bool(
        unsatisfied_orders
        or forbidden_hits
        or conflicts
        or strict_mutex
        or repeated_initial
        or not strict_route_correct
        or (
            expected_status == "blocked"
            and not exact_blockers
        )
    )
    semantic_gold_violated = bool(
        unsatisfied_orders
        or forbidden_hits
        or conflicts
        or semantic_mutex
        or repeated_initial
        or not semantic_route_correct
        or (
            expected_status == "blocked"
            and not exact_blockers
        )
    )

    exact_skill_selection = (
        skill_precision == 1.0
        and skill_recall == 1.0
        and not unknown_skills
        and not duplicate_skills
    )
    exact_departments = (
        department_precision == 1.0
        and department_recall == 1.0
        and not unknown_departments
        and len(departments) == len(set(departments))
    )
    no_tool_base = (
        use_skills is False
        and not sequence
        and not departments
        and not blocked_by
    )
    no_tool_correct = (
        expected_status == "no_tool"
        and no_tool_base
        and final_status == "no_tool"
        and not route_choice
    )
    semantic_no_tool_correct = (
        expected_status == "no_tool"
        and no_tool_base
        and final_status == "no_tool"
        and semantic_route_correct
    )
    blocked_flow_correct = (
        expected_status == "blocked"
        and use_skills_correct
        and final_status_correct
        and exact_blockers
        and not sequence
        and exact_departments
        and not forbidden_hits
        and not conflicts
        and not semantic_mutex
        and not unknown_skills
    )

    normal_routing = all(
        [
            format_valid,
            use_skills_correct,
            skill_precision == 1.0,
            skill_recall == 1.0,
            order_accuracy == 1.0,
            department_precision == 1.0,
            department_recall == 1.0,
            not unknown_skills,
            not unknown_departments,
            not duplicate_skills,
            not repeated_initial,
            not forbidden_hits,
            not conflicts,
            not semantic_mutex,
        ]
    )
    blocked_routing = all(
        [
            format_valid,
            use_skills_correct,
            not sequence,
            exact_departments,
            not unknown_skills,
            not unknown_departments,
            not forbidden_hits,
            not conflicts,
            not semantic_mutex,
        ]
    )
    no_tool_routing = format_valid and no_tool_base
    if expected_status == "blocked":
        skill_routing_success = blocked_routing
    elif expected_status == "no_tool":
        skill_routing_success = no_tool_routing
    else:
        skill_routing_success = normal_routing

    if expected_status == "no_tool":
        strict_success = no_tool_correct
        semantic_success = semantic_no_tool_correct
    elif expected_status == "blocked":
        strict_success = (
            blocked_flow_correct
            and strict_route_correct
            and not strict_gold_violated
        )
        semantic_success = (
            blocked_flow_correct
            and semantic_route_correct
            and not semantic_gold_violated
        )
    else:
        shared_normal = all(
            [
                format_valid,
                use_skills_correct,
                final_status_correct,
                exact_skill_selection,
                order_accuracy == 1.0,
                exact_departments,
                exact_blockers,
                not forbidden_hits,
                not conflicts,
                not repeated_initial,
            ]
        )
        strict_success = (
            shared_normal
            and strict_route_correct
            and not strict_mutex
            and not strict_gold_violated
        )
        semantic_success = (
            shared_normal
            and semantic_route_correct
            and not semantic_mutex
            and not semantic_gold_violated
        )

    if semantic_success and not skill_routing_success:
        raise RuntimeError(
            "STOPPED: semantic_functional_success=true while "
            f"skill_routing_success=false for {task['task_id']}"
        )

    if expected_status == "no_tool":
        control_success = semantic_no_tool_correct
    elif expected_status == "blocked":
        control_success = all(
            [
                format_valid,
                use_skills_correct,
                final_status_correct,
                exact_blockers,
                not continue_after_block,
                semantic_route_correct,
                not semantic_mutex,
            ]
        )
    else:
        control_success = all(
            [
                format_valid,
                use_skills_correct,
                final_status_correct,
                exact_blockers,
                semantic_route_correct,
                not semantic_mutex,
            ]
        )

    expression_audit = None
    if not strict_success and semantic_success:
        expression_audit = {
            "task_id": task["task_id"],
            "gold_route": expected_route,
            "raw_route_choice": route_choice,
            "raw_skill_sequence": sequence,
            "normalization_rules_applied": semantic_route[
                "normalization_rules_applied"
            ],
            "semantic_route_judgment": semantic_route,
            "other_strict_conditions_all_passed": True,
            "pure_expression_difference": True,
            "reason": (
                "Only exact route_choice expression differs; every non-route "
                "strict requirement passed under the frozen global rules."
            ),
        }

    return {
        "configuration": configuration,
        "run_id": run_id,
        "task_id": task["task_id"],
        "category": task["category"],
        "difficulty": task["difficulty"],
        "format_valid": format_valid,
        "format_errors": format_errors,
        "strict_functional_success": strict_success,
        "semantic_functional_success": semantic_success,
        "skill_routing_success": skill_routing_success,
        "control_success": control_success,
        "use_skills_correct": use_skills_correct,
        "final_status_correct": final_status_correct,
        "no_tool_correct": (
            no_tool_correct if expected_status == "no_tool" else ""
        ),
        "blocked_flow_correct": (
            blocked_flow_correct if expected_status == "blocked" else ""
        ),
        "skill_precision": round(skill_precision, 6),
        "skill_recall": round(skill_recall, 6),
        "skill_f1": round(skill_f1, 6),
        "department_precision": round(department_precision, 6),
        "department_recall": round(department_recall, 6),
        "department_f1": round(department_f1, 6),
        "required_order_accuracy": round(order_accuracy, 6),
        "strict_route_choice_correct": strict_route_correct,
        "semantic_route_choice_correct": semantic_route_correct,
        "blocked_reason_f1": round(blocker_f1, 6),
        "strict_gold_constraint_violated": strict_gold_violated,
        "semantic_gold_constraint_violated": semantic_gold_violated,
        "missing_required_skills": missing_required,
        "extra_skills": extra_skills,
        "unknown_skills": unknown_skills,
        "unknown_departments": unknown_departments,
        "duplicate_skills": duplicate_skills,
        "repeated_initial_skills": repeated_initial,
        "forbidden_hits": forbidden_hits,
        "hard_order_results": orders,
        "unsatisfied_order_pairs": unsatisfied_orders,
        "conflict_violations": conflicts,
        "strict_mutex_violations": strict_mutex,
        "semantic_mutex_violations": semantic_mutex,
        "missing_departments": missing_departments,
        "extra_departments": extra_departments,
        "missing_required_skill_count": len(missing_required),
        "extra_skill_count": len(extra_skills),
        "forbidden_skill_count": len(forbidden_hits),
        "repeated_completed_skill_count": len(repeated_initial),
        "unsatisfied_order_pair_count": len(unsatisfied_orders),
        "conflict_violation_count": len(conflicts),
        "mutex_violation_count": len(semantic_mutex),
        "continue_after_block_count": continue_after_block,
        "transport_failure_count": 0,
        "semantic_route_judgment": semantic_route,
        "semantic_expression_audit": expression_audit,
        "model_reason": prediction.get("reason", ""),
    }


def summarize_condition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("Cannot summarize an empty condition")
    semantic_without_routing = sum(
        row["semantic_functional_success"]
        and not row["skill_routing_success"]
        for row in rows
    )
    if semantic_without_routing:
        raise RuntimeError(
            "STOPPED: semantic=true but skill_routing=false in condition"
        )
    average_metrics = [
        "strict_functional_success",
        "semantic_functional_success",
        "skill_routing_success",
        "control_success",
        "skill_precision",
        "skill_recall",
        "skill_f1",
        "department_precision",
        "department_recall",
        "department_f1",
        "required_order_accuracy",
        "final_status_correct",
        "strict_route_choice_correct",
        "semantic_route_choice_correct",
        "blocked_reason_f1",
    ]
    result = {
        "configuration": rows[0]["configuration"],
        "run_id": rows[0]["run_id"],
        "n": len(rows),
    }
    for metric in average_metrics:
        result[metric] = round(
            sum(float(row[metric]) for row in rows) / len(rows), 6
        )
    result["no_tool_accuracy"] = _applicable_average(
        rows, "no_tool_correct"
    )
    result["blocked_flow_accuracy"] = _applicable_average(
        rows, "blocked_flow_correct"
    )
    result["strict_gold_constraint_violation_rate"] = round(
        sum(row["strict_gold_constraint_violated"] for row in rows)
        / len(rows),
        6,
    )
    result["semantic_gold_constraint_violation_rate"] = round(
        sum(row["semantic_gold_constraint_violated"] for row in rows)
        / len(rows),
        6,
    )
    for metric in (
        "missing_required_skill_count",
        "extra_skill_count",
        "forbidden_skill_count",
        "repeated_completed_skill_count",
        "unsatisfied_order_pair_count",
        "conflict_violation_count",
        "mutex_violation_count",
        "continue_after_block_count",
        "transport_failure_count",
    ):
        result[metric] = sum(row[metric] for row in rows)
    result["consistency_counts"] = {
        "strict_true_semantic_true": sum(
            row["strict_functional_success"]
            and row["semantic_functional_success"]
            for row in rows
        ),
        "strict_false_semantic_true": sum(
            not row["strict_functional_success"]
            and row["semantic_functional_success"]
            for row in rows
        ),
        "semantic_true_skill_routing_false": semantic_without_routing,
        "skill_routing_true_control_false": sum(
            row["skill_routing_success"]
            and not row["control_success"]
            for row in rows
        ),
        "strict_semantic_skill_routing_all_false": sum(
            not row["strict_functional_success"]
            and not row["semantic_functional_success"]
            and not row["skill_routing_success"]
            for row in rows
        ),
        "transport_or_schema_failure": sum(
            row["transport_failure_count"] or not row["format_valid"]
            for row in rows
        ),
    }
    result["strict_false_semantic_true_audit_count"] = sum(
        row["semantic_expression_audit"] is not None for row in rows
    )
    return result


def _applicable_average(
    rows: list[dict[str, Any]], metric: str
) -> float | str:
    values = [row[metric] for row in rows if row[metric] != ""]
    if not values:
        return ""
    return round(sum(float(value) for value in values) / len(values), 6)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(rows[0])
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        json.dumps(value, ensure_ascii=False)
                        if isinstance(value, (list, dict))
                        else value
                    )
                    for key, value in row.items()
                }
            )


def command_evaluate(args: argparse.Namespace) -> int:
    gold = load_json(Path(args.gold))
    tasks = {task["task_id"]: task for task in gold["tasks"]}
    prediction_dir = Path(args.predictions)
    rows = []
    for task_id, task in tasks.items():
        path = prediction_dir / f"{task_id}.json"
        if path.is_file():
            try:
                prediction = load_json(path)
            except Exception as exc:
                prediction = {"task_id": task_id, "_parse_error": str(exc)}
        else:
            prediction = {
                "task_id": task_id,
                "_parse_error": "missing_prediction",
            }
        rows.append(
            evaluate_record(
                prediction,
                task,
                gold,
                args.configuration,
                args.run_id,
            )
        )
    summary = summarize_condition(rows)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=False)
    (output / "per_task_results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(output / "per_task_results.csv", rows)
    (output / "condition_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    audits = [
        row["semantic_expression_audit"]
        for row in rows
        if row["semantic_expression_audit"] is not None
    ]
    (output / "semantic_expression_audit.json").write_text(
        json.dumps(audits, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--gold", default=str(DEFAULT_GOLD))
    evaluate.add_argument("--predictions", required=True)
    evaluate.add_argument("--configuration", required=True)
    evaluate.add_argument("--run-id", required=True)
    evaluate.add_argument("--output-dir", required=True)
    evaluate.set_defaults(func=command_evaluate)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
