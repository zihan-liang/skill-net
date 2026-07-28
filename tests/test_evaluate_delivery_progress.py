#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "business-project-delivery-tracking"
    / "scripts"
    / "evaluate_delivery_progress.py"
)
SPEC = spec_from_file_location("evaluate_delivery_progress", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class DeliveryProgressEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "contract_id": "CON-1",
            "project_id": "PROJ-1",
            "as_of_date": "2026-07-28",
            "milestones": [
                {
                    "milestone_id": "M1",
                    "title": "Design approved",
                    "owner": "Delivery Lead",
                    "weight_percent": "40",
                    "due_date": "2026-07-20",
                    "status": "completed",
                    "progress_percent": "100",
                    "evidence_reference": "E-M1",
                },
                {
                    "milestone_id": "M2",
                    "title": "Configuration",
                    "owner": "Engineer",
                    "weight_percent": "35",
                    "due_date": "2026-08-05",
                    "status": "in_progress",
                    "progress_percent": "50",
                    "evidence_reference": "E-M2",
                },
                {
                    "milestone_id": "M3",
                    "title": "Customer review",
                    "owner": "Customer Success",
                    "weight_percent": "25",
                    "due_date": "2026-08-15",
                    "status": "planned",
                    "progress_percent": "0",
                    "evidence_reference": "",
                },
            ],
        }

    def test_returns_hand_checked_weighted_completion(self):
        result = MODULE.evaluate_delivery_progress(self.data)

        self.assertEqual(result["weighted_completion_percent"], "57.50")
        self.assertEqual(result["blocking_findings"], [])
        self.assertTrue(result["automated_health_passed"])
        self.assertEqual(result["delivery_status"], "on_track_human_review")

    def test_rejects_weights_that_do_not_total_100(self):
        milestones = [self.data["milestones"][0], self.data["milestones"][1]]

        with self.assertRaisesRegex(ValueError, "milestone weights must sum to 100"):
            MODULE.evaluate_delivery_progress({**self.data, "milestones": milestones})

    def test_rejects_duplicate_milestone_ids(self):
        milestones = [
            self.data["milestones"][0],
            {**self.data["milestones"][1], "milestone_id": "M1"},
            self.data["milestones"][2],
        ]

        with self.assertRaisesRegex(ValueError, "duplicate milestone_id: M1"):
            MODULE.evaluate_delivery_progress({**self.data, "milestones": milestones})

    def test_reports_overdue_and_blocked_milestones(self):
        milestones = [
            self.data["milestones"][0],
            {
                **self.data["milestones"][1],
                "status": "blocked",
                "due_date": "2026-07-27",
                "progress_percent": "50",
            },
            self.data["milestones"][2],
        ]

        result = MODULE.evaluate_delivery_progress({**self.data, "milestones": milestones})

        self.assertIn("blocked milestone: M2", result["blocking_findings"])
        self.assertIn("overdue milestone: M2", result["blocking_findings"])
        self.assertEqual(result["delivery_status"], "needs_attention")

    def test_rejects_status_progress_mismatch(self):
        milestones = [
            {**self.data["milestones"][0], "progress_percent": "90"},
            self.data["milestones"][1],
            self.data["milestones"][2],
        ]

        with self.assertRaisesRegex(ValueError, "completed milestone M1 progress must be 100"):
            MODULE.evaluate_delivery_progress({**self.data, "milestones": milestones})

    def test_missing_completion_evidence_blocks_health(self):
        milestones = [
            {**self.data["milestones"][0], "evidence_reference": ""},
            self.data["milestones"][1],
            self.data["milestones"][2],
        ]

        result = MODULE.evaluate_delivery_progress({**self.data, "milestones": milestones})

        self.assertIn("missing completion evidence: M1", result["blocking_findings"])
        self.assertFalse(result["automated_health_passed"])

    def test_rejects_invalid_status_and_progress_range(self):
        with self.assertRaisesRegex(ValueError, "unsupported milestone status"):
            MODULE.evaluate_delivery_progress(
                {**self.data, "milestones": [{**self.data["milestones"][0], "status": "unknown"}, *self.data["milestones"][1:]]}
            )
        with self.assertRaisesRegex(ValueError, "progress_percent must be between 0 and 100"):
            MODULE.evaluate_delivery_progress(
                {**self.data, "milestones": [{**self.data["milestones"][0], "progress_percent": "101"}, *self.data["milestones"][1:]]}
            )


if __name__ == "__main__":
    unittest.main()
