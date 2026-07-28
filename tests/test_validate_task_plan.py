#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "technology-task-breakdown"
    / "scripts"
    / "validate_task_plan.py"
)
SPEC = spec_from_file_location("validate_task_plan", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class TaskPlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "task_plan_id": "PLAN-1",
            "design_id": "DESIGN-1",
            "design_approval_reference": "APP-DESIGN-1",
            "tasks": [
                {
                    "task_id": "T1",
                    "title": "Define schema",
                    "owner": "Engineer A",
                    "deliverable": "Versioned schema",
                    "acceptance_criteria": ["Schema validation passes"],
                    "estimate_hours": "2",
                    "dependencies": [],
                },
                {
                    "task_id": "T3",
                    "title": "Add documentation",
                    "owner": "Engineer B",
                    "deliverable": "API reference",
                    "acceptance_criteria": ["Examples execute successfully"],
                    "estimate_hours": "1.5",
                    "dependencies": ["T1"],
                },
                {
                    "task_id": "T2",
                    "title": "Implement endpoint",
                    "owner": "Engineer A",
                    "deliverable": "Tested endpoint",
                    "acceptance_criteria": ["Contract tests pass"],
                    "estimate_hours": "3.5",
                    "dependencies": ["T1"],
                },
            ],
        }

    def test_returns_deterministic_dependency_order_and_total(self):
        result = MODULE.validate_task_plan(self.plan)

        self.assertEqual(result["execution_order"], ["T1", "T2", "T3"])
        self.assertEqual(result["total_estimate_hours"], "7.00")
        self.assertEqual(result["task_count"], 3)
        self.assertEqual(result["assignment_status"], "human_review_required")

    def test_rejects_duplicate_task_ids(self):
        plan = {
            **self.plan,
            "tasks": [self.plan["tasks"][0], {**self.plan["tasks"][1], "task_id": "T1"}],
        }

        with self.assertRaisesRegex(ValueError, "duplicate task_id: T1"):
            MODULE.validate_task_plan(plan)

    def test_rejects_unknown_dependency(self):
        plan = {
            **self.plan,
            "tasks": [
                {**self.plan["tasks"][0], "dependencies": ["T-MISSING"]}
            ],
        }

        with self.assertRaisesRegex(ValueError, "unknown dependency T-MISSING"):
            MODULE.validate_task_plan(plan)

    def test_rejects_dependency_cycle(self):
        plan = {
            **self.plan,
            "tasks": [
                {**self.plan["tasks"][0], "dependencies": ["T2"]},
                {**self.plan["tasks"][2], "dependencies": ["T1"]},
            ],
        }

        with self.assertRaisesRegex(ValueError, "task dependency cycle"):
            MODULE.validate_task_plan(plan)

    def test_rejects_missing_owner(self):
        plan = {
            **self.plan,
            "tasks": [{**self.plan["tasks"][0], "owner": ""}],
        }

        with self.assertRaisesRegex(ValueError, "missing task fields: owner"):
            MODULE.validate_task_plan(plan)

    def test_rejects_empty_acceptance_criteria(self):
        plan = {
            **self.plan,
            "tasks": [{**self.plan["tasks"][0], "acceptance_criteria": []}],
        }

        with self.assertRaisesRegex(ValueError, "acceptance_criteria must be a non-empty list"):
            MODULE.validate_task_plan(plan)

    def test_rejects_non_positive_estimate(self):
        plan = {
            **self.plan,
            "tasks": [{**self.plan["tasks"][0], "estimate_hours": "0"}],
        }

        with self.assertRaisesRegex(ValueError, "estimate_hours must be positive"):
            MODULE.validate_task_plan(plan)


if __name__ == "__main__":
    unittest.main()
