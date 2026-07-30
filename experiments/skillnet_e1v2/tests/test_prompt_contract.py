#!/usr/bin/env python3
"""E1-v2 runner prompt and fixed eight-field schema tests."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[3]
E1V2_DIR = ROOT / "experiments" / "skillnet_e1v2"
RUNNER_SPEC = importlib.util.spec_from_file_location(
    "run_condition_e1v2", E1V2_DIR / "run_condition.py"
)
assert RUNNER_SPEC and RUNNER_SPEC.loader
RUNNER = importlib.util.module_from_spec(RUNNER_SPEC)
RUNNER_SPEC.loader.exec_module(RUNNER)


class E1V2PromptContractTests(unittest.TestCase):
    def test_schema_has_exactly_eight_prediction_fields(self) -> None:
        schema = json.loads(
            (E1V2_DIR / "prediction_schema_e1v2.json").read_text(encoding="utf-8")
        )
        expected = {
            "task_id",
            "use_skills",
            "selected_departments",
            "skill_sequence",
            "final_status",
            "blocked_by",
            "route_choice",
            "reason",
        }
        self.assertEqual(expected, set(schema["required"]))
        self.assertEqual(expected, set(schema["properties"]))
        self.assertFalse(schema["additionalProperties"])

    def test_child_prompt_freezes_route_status_and_sequence_semantics(self) -> None:
        prompt = RUNNER.build_child_prompt(
            "GT01_SINGLE",
            "测试任务",
            {
                "configuration": "A",
                "catalogue_size": 10,
                "skills": [],
            },
        )
        for text in (
            '{"acceptance_route":"technical_acceptance"}',
            '{"acceptance_route":"business_acceptance"}',
            '{"build_or_buy":"internal_development"}',
            '{"build_or_buy":"external_procurement"}',
            "final_status=blocked 时，skill_sequence 必须为空数组",
            "只包含接下来真实应该执行的 Skills",
            "不包含已经完成的 Skills",
            "不填写被阻止执行的下游 Skills",
            "仅仅因为路线中还有未来步骤尚未完成，不等于 blocked",
        ):
            self.assertIn(text, prompt)
        for forbidden in (
            "delivery_mode",
            "development_mode",
            "single_primary_acceptance_route",
            "internal_build",
        ):
            self.assertIn(f"不得使用 `{forbidden}`", prompt)

    def test_schema_accepts_new_short_task_ids(self) -> None:
        schema = json.loads(
            (E1V2_DIR / "prediction_schema_e1v2.json").read_text(encoding="utf-8")
        )
        prediction = {
            "task_id": "E1V2_GT03_PROC_SHORT",
            "use_skills": True,
            "selected_departments": ["procurement-agent"],
            "skill_sequence": ["procurement-quote-comparison"],
            "final_status": "completed",
            "blocked_by": [],
            "route_choice": {},
            "reason": "fixture",
        }
        jsonschema.validate(prediction, schema)


if __name__ == "__main__":
    unittest.main()
