#!/usr/bin/env python3
"""Regression tests for the canonical-ID bilingual SkillNet evaluator."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

import jsonschema


EVALUATION_DIR = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = EVALUATION_DIR.parent
GOLD = json.loads((PACKAGE_ROOT / "02_Gold_Standard_21_V4.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((EVALUATION_DIR / "prediction_schema.json").read_text(encoding="utf-8"))
MAPPING = json.loads((PACKAGE_ROOT / "skill_name_map.json").read_text(encoding="utf-8"))

SPEC = importlib.util.spec_from_file_location(
    "evaluate_skillnet", EVALUATION_DIR / "evaluate_skillnet.py"
)
assert SPEC and SPEC.loader
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def perfect_prediction(task: dict) -> dict:
    return {
        "task_id": task["task_id"],
        "use_skills": task["use_skills"],
        "selected_departments": list(task["required_departments"]),
        "skill_sequence": list(task["canonical_sequence"]),
        "final_status": task["expected_final_status"],
        "blocked_by": list(task["expected_blocked_by"]),
        "route_choice": dict(task["expected_route_choice"]),
        "reason": "Deterministic regression fixture.",
    }


class SkillNetEvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = {task["task_id"]: task for task in GOLD["tasks"]}
        cls.skill_ids = set(GOLD["skill_catalog"])
        cls.department_ids = set(GOLD["department_catalog"])

    def evaluate(self, task_id: str, prediction: dict) -> dict:
        return EVALUATOR.evaluate_record(
            prediction,
            self.tasks[task_id],
            GOLD,
            configuration="TEST",
            run_id="1",
        )

    def test_package_is_internally_valid(self) -> None:
        report = EVALUATOR.validate_package(GOLD)
        self.assertTrue(report["valid"], report)
        self.assertEqual(21, report["task_count"])
        self.assertEqual(46, report["skill_count"])
        self.assertEqual([], report["errors"])
        self.assertEqual([], report["warnings"])

    def test_all_21_tasks_exist(self) -> None:
        self.assertEqual(21, len(self.tasks))
        self.assertEqual(21, GOLD["task_count"])
        self.assertEqual({f"GT{number:02d}" for number in range(1, 22)}, {
            task_id.split("_", 1)[0] for task_id in self.tasks
        })

    def test_every_task_has_complete_english_and_chinese_text(self) -> None:
        for task in GOLD["tasks"]:
            for field in (
                "title_en",
                "title_zh",
                "prompt_en",
                "prompt_zh",
                "gold_rationale_en",
                "gold_rationale_zh",
            ):
                self.assertIsInstance(task[field], str)
                self.assertTrue(task[field].strip(), (task["task_id"], field))
            prompt_file = PACKAGE_ROOT / "prompts" / f"{task['task_id']}.txt"
            prompt_text = prompt_file.read_text(encoding="utf-8")
            self.assertIn("English task prompt", prompt_text)
            self.assertIn("中文任务", prompt_text)
            self.assertIn(task["prompt_en"], prompt_text)
            self.assertIn(task["prompt_zh"], prompt_text)

    def test_schema_accepts_completed_blocked_and_no_tool(self) -> None:
        for task_id in ("GT01_SINGLE", "GT16_SPECIAL_SUPPLIER_FAIL", "GT19_NO_TOOL_CLEAR"):
            jsonschema.validate(perfect_prediction(self.tasks[task_id]), SCHEMA)

    def test_schema_rejects_unknown_skill(self) -> None:
        prediction = perfect_prediction(self.tasks["GT01_SINGLE"])
        prediction["skill_sequence"] = ["procurement-not-a-real-skill"]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(prediction, SCHEMA)

    def test_gold_perfect_predictions_score_100_percent(self) -> None:
        rows = [
            self.evaluate(task["task_id"], perfect_prediction(task))
            for task in GOLD["tasks"]
        ]
        for row in rows:
            self.assertTrue(row["functional_success"], row)
            self.assertTrue(row["clean_success"], row)
            self.assertEqual(1.0, row["skill_precision"], row)
            self.assertEqual(1.0, row["skill_recall"], row)
            self.assertEqual(1.0, row["skill_f1"], row)
            self.assertEqual(1.0, row["department_precision"], row)
            self.assertEqual(1.0, row["department_recall"], row)
            self.assertEqual(1.0, row["department_f1"], row)
            self.assertEqual(1.0, row["required_order_accuracy"], row)
            self.assertFalse(row["gold_constraint_violated"], row)
        summary = EVALUATOR.summarize(rows, ["configuration", "run_id"])[0]
        for metric in (
            "functional_success",
            "clean_success",
            "skill_precision",
            "skill_recall",
            "skill_f1",
            "department_precision",
            "department_recall",
            "department_f1",
            "required_order_accuracy",
            "no_tool_accuracy",
            "blocked_flow_accuracy",
        ):
            self.assertEqual(1.0, summary[metric], (metric, summary))
        self.assertEqual(0.0, summary["gold_constraint_violation_rate"])

    def test_valid_alternative_partial_order_is_accepted(self) -> None:
        task = self.tasks["GT14_CROSS_PAYMENT_PERFORMANCE"]
        prediction = perfect_prediction(task)
        prediction["skill_sequence"] = [
            "finance-invoice-verification",
            "finance-payment-approval",
            "procurement-supplier-evaluation",
            "finance-accounting",
        ]
        result = self.evaluate(task["task_id"], prediction)
        self.assertTrue(result["functional_success"], result)
        self.assertTrue(result["clean_success"], result)
        self.assertEqual(1.0, result["required_order_accuracy"])

    def test_invalid_json_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.jsonl"
            path.write_text('{"task_id": "GT01_SINGLE", invalid}\\n', encoding="utf-8")
            records = EVALUATOR.load_predictions(path)
        self.assertEqual(1, len(records))
        self.assertIn("_parse_error", records[0])

    def test_unknown_skill_is_detected(self) -> None:
        task = self.tasks["GT01_SINGLE"]
        prediction = perfect_prediction(task)
        prediction["skill_sequence"].append("procurement-not-a-real-skill")
        result = self.evaluate(task["task_id"], prediction)
        self.assertIn("UNKNOWN_SKILL", [result["primary_failure"], *result["secondary_failures"]])
        self.assertFalse(result["functional_success"])

    def test_missing_required_skill_is_detected(self) -> None:
        task = self.tasks["GT03_PROC_GOAL"]
        prediction = perfect_prediction(task)
        prediction["skill_sequence"].remove("procurement-supplier-scoring")
        result = self.evaluate(task["task_id"], prediction)
        self.assertIn(
            "MISSING_REQUIRED_SKILL",
            [result["primary_failure"], *result["secondary_failures"]],
        )
        self.assertFalse(result["functional_success"])

    def test_order_violation_is_detected(self) -> None:
        task = self.tasks["GT02_FIN_GOAL"]
        prediction = perfect_prediction(task)
        prediction["skill_sequence"].reverse()
        result = self.evaluate(task["task_id"], prediction)
        self.assertIn("ORDER_VIOLATION", [result["primary_failure"], *result["secondary_failures"]])
        self.assertFalse(result["functional_success"])

    def test_blocked_flow_error_and_continuation_are_detected(self) -> None:
        task = self.tasks["GT16_SPECIAL_SUPPLIER_FAIL"]
        prediction = perfect_prediction(task)
        prediction["skill_sequence"] = ["procurement-supplier-selection"]
        result = self.evaluate(task["task_id"], prediction)
        failures = [result["primary_failure"], *result["secondary_failures"]]
        self.assertIn("CONFLICT_VIOLATION", failures)
        self.assertIn("CONTINUE_AFTER_BLOCK", failures)
        self.assertFalse(result["blocked_flow_correct"])
        self.assertFalse(result["functional_success"])

    def test_false_tool_activation_is_detected(self) -> None:
        task = self.tasks["GT20_NO_TOOL_FINANCE"]
        prediction = perfect_prediction(task)
        prediction.update(
            {
                "use_skills": True,
                "selected_departments": ["finance-agent"],
                "skill_sequence": ["finance-budget-check"],
                "final_status": "completed",
                "reason": "Incorrectly activated a finance Skill.",
            }
        )
        result = self.evaluate(task["task_id"], prediction)
        self.assertIn(
            "FALSE_TOOL_ACTIVATION",
            [result["primary_failure"], *result["secondary_failures"]],
        )
        self.assertFalse(result["no_tool_correct"])
        self.assertFalse(result["functional_success"])

    def test_machine_fields_use_only_canonical_ids(self) -> None:
        cjk = re.compile(r"[\u3400-\u9fff]")
        for task in GOLD["tasks"]:
            machine_skill_values = [
                *task["required_skills"],
                *task["optional_skills"],
                *task["forbidden_skills"],
                *task["canonical_sequence"],
                *task["initial_skill_states"].keys(),
                *task["expected_blocked_by"],
            ]
            for pair in task["hard_order_constraints"]:
                machine_skill_values.extend([pair["before"], pair["after"]])
            for rule in task["task_constraints"]:
                if "trigger_skill" in rule:
                    machine_skill_values.append(rule["trigger_skill"])
                machine_skill_values.extend(rule.get("blocked_skills", []))
                machine_skill_values.extend(rule.get("forbidden_route_skills", []))
            self.assertFalse(any(cjk.search(value) for value in machine_skill_values), task["task_id"])
            self.assertTrue(set(machine_skill_values) <= self.skill_ids, task["task_id"])
            self.assertTrue(set(task["required_departments"]) <= self.department_ids)

    def test_mapping_matches_authoritative_main(self) -> None:
        main_root_value = os.environ.get("SKILLNET_MAIN_ROOT")
        if not main_root_value:
            self.skipTest("SKILLNET_MAIN_ROOT not provided")
        main_root = Path(main_root_value)
        main_skill_ids = {
            path.parent.name for path in (main_root / ".agents" / "skills").glob("*/SKILL.md")
        }
        relation_data = json.loads((main_root / "skill_relations.json").read_text(encoding="utf-8"))
        main_department_ids = {entry["parent"] for entry in relation_data["contains"]}
        mapping_ids = {entry["id"] for entry in MAPPING["skills"]}
        mapping_department_ids = {entry["id"] for entry in MAPPING["departments"]}
        self.assertEqual(main_skill_ids, self.skill_ids)
        self.assertEqual(main_skill_ids, mapping_ids)
        self.assertEqual(main_department_ids, self.department_ids)
        self.assertEqual(main_department_ids, mapping_department_ids)
        for entry in MAPPING["skills"]:
            skill_text = (
                main_root / ".agents" / "skills" / entry["id"] / "SKILL.md"
            ).read_text(encoding="utf-8")
            frontmatter_name = re.search(r"(?m)^name:\s*(\S+)\s*$", skill_text)
            h1_title = re.search(r"(?m)^# (.+)$", skill_text)
            self.assertIsNotNone(frontmatter_name)
            self.assertIsNotNone(h1_title)
            self.assertEqual(entry["id"], frontmatter_name.group(1))
            self.assertEqual(entry["name_en"], h1_title.group(1).strip())

    def test_original_gold_semantics_are_preserved(self) -> None:
        original_root_value = os.environ.get("SKILLNET_ORIGINAL_PACKAGE")
        if not original_root_value:
            self.skipTest("SKILLNET_ORIGINAL_PACKAGE not provided")
        original = json.loads(
            (Path(original_root_value) / "02_Gold_Standard_21_V4.json").read_text(
                encoding="utf-8"
            )
        )
        original_tasks = {task["task_id"]: task for task in original["tasks"]}
        zh_to_id = {entry["display_name"]: entry["id"] for entry in MAPPING["skills"]}
        legacy_department_to_id = {
            "Finance Agent": "finance-agent",
            "Procurement Agent": "procurement-agent",
            "Technology Agent": "technology-agent",
            "Business Agent": "business-agent",
            "HR Agent": "hr-agent",
        }

        def map_constraint(rule: dict) -> dict:
            mapped = copy.deepcopy(rule)
            if "trigger_skill" in mapped:
                mapped["trigger_skill"] = zh_to_id[mapped["trigger_skill"]]
            if "blocked_skills" in mapped:
                mapped["blocked_skills"] = [zh_to_id[value] for value in mapped["blocked_skills"]]
            if "forbidden_route_skills" in mapped:
                mapped["forbidden_route_skills"] = [
                    zh_to_id[value] for value in mapped["forbidden_route_skills"]
                ]
            return mapped

        self.assertEqual(set(original_tasks), set(self.tasks))
        for task_id, task in self.tasks.items():
            legacy = original_tasks[task_id]
            self.assertEqual(legacy["title"], task["title_zh"])
            self.assertEqual(legacy["prompt"], task["prompt_zh"])
            self.assertEqual(legacy["use_skills"], task["use_skills"])
            self.assertEqual(
                [legacy_department_to_id[value] for value in legacy["required_departments"]],
                task["required_departments"],
            )
            for field in ("required_skills", "optional_skills"):
                self.assertEqual([zh_to_id[value] for value in legacy[field]], task[field])
            legacy_forbidden = legacy["forbidden_skills"]
            self.assertEqual("ALL_BUSINESS_SKILLS" in legacy_forbidden, task["forbid_all_skills"])
            self.assertEqual(
                [zh_to_id[value] for value in legacy_forbidden if value != "ALL_BUSINESS_SKILLS"],
                task["forbidden_skills"],
            )
            self.assertEqual(
                [zh_to_id[value] for value in legacy["canonical_sequence"]],
                task["canonical_sequence"],
            )
            self.assertEqual(
                {zh_to_id[key]: value for key, value in legacy["initial_skill_states"].items()},
                task["initial_skill_states"],
            )
            self.assertEqual(
                [zh_to_id[value] for value in legacy["expected_blocked_by"]],
                task["expected_blocked_by"],
            )
            self.assertEqual(legacy["expected_final_status"], task["expected_final_status"])
            self.assertEqual(legacy["expected_route_choice"], task["expected_route_choice"])
            expected_order = []
            for pair in legacy["hard_order_constraints"]:
                mapped = copy.deepcopy(pair)
                mapped["before"] = zh_to_id[mapped["before"]]
                mapped["after"] = zh_to_id[mapped["after"]]
                expected_order.append(mapped)
            self.assertEqual(expected_order, task["hard_order_constraints"])
            self.assertEqual(
                [map_constraint(rule) for rule in legacy["task_constraints"]],
                task["task_constraints"],
            )


if __name__ == "__main__":
    unittest.main()
