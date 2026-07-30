#!/usr/bin/env python3
"""Metric-split regression tests for the isolated E1-v2 evaluator."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
E1V2_DIR = ROOT / "experiments" / "skillnet_e1v2"
GOLD_PATH = ROOT / "SkillNet_Gold_Tasks_V4" / "e1v2" / "E1V2_Gold_21.json"
SPEC = importlib.util.spec_from_file_location(
    "evaluate_skillnet_e1v2", E1V2_DIR / "evaluate_e1v2.py"
)
assert SPEC and SPEC.loader
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)
GOLD = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
TASKS = {task["task_id"]: task for task in GOLD["tasks"]}


def perfect(task_id: str) -> dict:
    task = TASKS[task_id]
    return {
        "task_id": task_id,
        "use_skills": task["use_skills"],
        "selected_departments": list(task["required_departments"]),
        "skill_sequence": list(task["canonical_sequence"]),
        "final_status": task["expected_final_status"],
        "blocked_by": list(task["expected_blocked_by"]),
        "route_choice": dict(task["expected_route_choice"]),
        "reason": "Frozen test fixture.",
    }


def score(task_id: str, prediction: dict | None, **kwargs: object) -> dict:
    return EVALUATOR.evaluate_record(
        prediction,
        TASKS[task_id],
        GOLD,
        configuration="TEST",
        run_id="setup",
        **kwargs,
    )


class E1V2EvaluatorMetricTests(unittest.TestCase):
    def test_gt13_alias_key_is_semantic_only_difference(self) -> None:
        prediction = perfect("GT13_CROSS_INTERNAL_DEV_STAFF_DATA")
        prediction["route_choice"] = {"delivery_mode": "internal_development"}
        row = score(prediction["task_id"], prediction)
        self.assertFalse(row["strict_functional_success"])
        self.assertTrue(row["semantic_functional_success"])
        self.assertTrue(row["skill_routing_success"])
        self.assertTrue(
            row["semantic_expression_audit"]["pure_expression_difference"]
        )
        self.assertTrue(
            row["semantic_expression_audit"][
                "other_strict_conditions_all_passed"
            ]
        )

    def test_gt18_alias_value_is_semantic_only_difference(self) -> None:
        prediction = perfect("GT18_SPECIAL_BUILD_OR_BUY")
        prediction["route_choice"] = {"build_or_buy": "build"}
        row = score(prediction["task_id"], prediction)
        self.assertFalse(row["strict_functional_success"])
        self.assertTrue(row["semantic_functional_success"])
        self.assertTrue(row["skill_routing_success"])

    def test_semantic_route_cannot_rescue_missing_skill(self) -> None:
        prediction = perfect("GT09_CROSS_BUS_SERVICE_PAYMENT")
        prediction["skill_sequence"].remove("finance-accounting")
        row = score(prediction["task_id"], prediction)
        self.assertFalse(row["strict_functional_success"])
        self.assertFalse(row["semantic_functional_success"])
        self.assertFalse(row["skill_routing_success"])

    def test_wrong_final_status_does_not_control_skill_routing(self) -> None:
        prediction = perfect("GT08_CROSS_TECH_DELIVERY_PAYMENT")
        prediction["final_status"] = "blocked"
        prediction["blocked_by"] = ["technology-test-acceptance"]
        row = score(prediction["task_id"], prediction)
        self.assertFalse(row["strict_functional_success"])
        self.assertFalse(row["semantic_functional_success"])
        self.assertTrue(row["skill_routing_success"])
        self.assertFalse(row["control_success"])

    def test_continue_after_block_fails_all_success_metrics(self) -> None:
        prediction = perfect("GT16_SPECIAL_SUPPLIER_FAIL")
        prediction["skill_sequence"] = [
            "procurement-supplier-selection",
            "procurement-contract-generation",
        ]
        row = score(prediction["task_id"], prediction)
        self.assertFalse(row["strict_functional_success"])
        self.assertFalse(row["semantic_functional_success"])
        self.assertFalse(row["skill_routing_success"])
        self.assertFalse(row["control_success"])
        self.assertEqual(1, row["continue_after_block_count"])

    def test_transport_empty_and_invalid_json_fail_all(self) -> None:
        for prediction, kwargs in (
            (None, {"transport_failure": True}),
            ({"task_id": "GT01_SINGLE", "_parse_error": "empty_response"}, {}),
            ({"task_id": "GT01_SINGLE", "_parse_error": "invalid_json"}, {}),
        ):
            row = score("GT01_SINGLE", prediction, **kwargs)
            self.assertFalse(row["strict_functional_success"])
            self.assertFalse(row["semantic_functional_success"])
            self.assertFalse(row["skill_routing_success"])
            self.assertFalse(row["control_success"])

    def test_genuinely_wrong_route_fails_strict_and_semantic(self) -> None:
        prediction = perfect("GT09_CROSS_BUS_SERVICE_PAYMENT")
        prediction["skill_sequence"] = [
            skill
            for skill in prediction["skill_sequence"]
            if skill != "business-acceptance"
        ]
        prediction["skill_sequence"].insert(1, "technology-test-acceptance")
        prediction["selected_departments"] = [
            "procurement-agent", "technology-agent", "finance-agent"
        ]
        prediction["route_choice"] = {"acceptance_route": "technical_acceptance"}
        row = score(prediction["task_id"], prediction)
        self.assertFalse(row["strict_functional_success"])
        self.assertFalse(row["semantic_functional_success"])

    def test_both_mutex_routes_fail_routing(self) -> None:
        prediction = perfect("GT08_CROSS_TECH_DELIVERY_PAYMENT")
        prediction["skill_sequence"].insert(2, "business-acceptance")
        prediction["selected_departments"].append("business-agent")
        row = score(prediction["task_id"], prediction)
        self.assertFalse(row["strict_functional_success"])
        self.assertFalse(row["semantic_functional_success"])
        self.assertFalse(row["skill_routing_success"])
        self.assertGreater(row["mutex_violation_count"], 0)

    def test_no_tool_harmless_route_redundancy_is_semantically_accepted(self) -> None:
        prediction = perfect("GT19_NO_TOOL_CLEAR")
        prediction["route_choice"] = {"tool_decision": "no_tool"}
        row = score(prediction["task_id"], prediction)
        self.assertFalse(row["strict_functional_success"])
        self.assertTrue(row["semantic_functional_success"])
        self.assertTrue(row["skill_routing_success"])

    def test_semantic_route_alias_does_not_pollute_semantic_constraints(self) -> None:
        prediction = perfect("GT13_CROSS_INTERNAL_DEV_STAFF_DATA")
        prediction["route_choice"] = {"development_mode": "build"}
        row = score(prediction["task_id"], prediction)
        self.assertTrue(row["semantic_route_choice_correct"])
        self.assertFalse(row["semantic_gold_constraint_violated"])
        self.assertTrue(row["semantic_functional_success"])

    def test_semantic_success_always_implies_skill_routing_success(self) -> None:
        rows = [score(task_id, perfect(task_id)) for task_id in TASKS]
        self.assertFalse(
            any(
                row["semantic_functional_success"]
                and not row["skill_routing_success"]
                for row in rows
            )
        )

    def test_condition_consistency_counts_and_audit_are_emitted(self) -> None:
        alias = perfect("GT13_CROSS_INTERNAL_DEV_STAFF_DATA")
        alias["route_choice"] = {"delivery_mode": "internal_development"}
        rows = [
            score(alias["task_id"], alias),
            score("GT01_SINGLE", perfect("GT01_SINGLE")),
        ]
        summary = EVALUATOR.summarize_condition(rows)
        self.assertEqual(
            1, summary["consistency_counts"]["strict_true_semantic_true"]
        )
        self.assertEqual(
            1, summary["consistency_counts"]["strict_false_semantic_true"]
        )
        self.assertEqual(
            0,
            summary["consistency_counts"][
                "semantic_true_skill_routing_false"
            ],
        )
        self.assertEqual(1, summary["strict_false_semantic_true_audit_count"])


if __name__ == "__main__":
    unittest.main()
