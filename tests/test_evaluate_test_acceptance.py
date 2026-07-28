#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "technology-test-acceptance"
    / "scripts"
    / "evaluate_test_acceptance.py"
)
SPEC = spec_from_file_location("evaluate_test_acceptance", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class TestAcceptanceEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "test_run_id": "RUN-1",
            "system_id": "SYS-1",
            "version_id": "VER-1",
            "environment": "staging",
            "required_suites": ["unit", "integration"],
            "minimum_pass_rate_percent": "95",
            "minimum_coverage_percent": "80",
            "coverage_percent": "85",
            "suites": [
                {
                    "suite_id": "unit",
                    "executed": 60,
                    "passed": 60,
                    "failed": 0,
                    "skipped": 0,
                    "evidence_reference": "TEST-UNIT-1",
                },
                {
                    "suite_id": "integration",
                    "executed": 40,
                    "passed": 38,
                    "failed": 0,
                    "skipped": 2,
                    "evidence_reference": "TEST-INT-1",
                },
            ],
            "defects": [],
        }

    def test_recomputes_hand_checked_totals_and_pass_rate(self):
        result = MODULE.evaluate_test_acceptance(self.data)

        self.assertEqual(result["totals"], {"executed": 100, "passed": 98, "failed": 0, "skipped": 2})
        self.assertEqual(result["pass_rate_percent"], "98.00")
        self.assertTrue(result["automated_gate_passed"])
        self.assertEqual(result["acceptance_status"], "human_review_required")

    def test_missing_required_suite_blocks_acceptance(self):
        data = {**self.data, "suites": [self.data["suites"][0]]}

        result = MODULE.evaluate_test_acceptance(data)

        self.assertFalse(result["automated_gate_passed"])
        self.assertIn("missing required suite: integration", result["blocking_findings"])
        self.assertEqual(result["acceptance_status"], "blocked")

    def test_missing_suite_evidence_blocks_acceptance(self):
        suites = [self.data["suites"][0], {**self.data["suites"][1], "evidence_reference": ""}]

        result = MODULE.evaluate_test_acceptance({**self.data, "suites": suites})

        self.assertIn("missing evidence for suite: integration", result["blocking_findings"])

    def test_rejects_inconsistent_suite_counts(self):
        suites = [{**self.data["suites"][0], "executed": 61}, self.data["suites"][1]]

        with self.assertRaisesRegex(ValueError, "suite unit counts do not reconcile"):
            MODULE.evaluate_test_acceptance({**self.data, "suites": suites})

    def test_failed_test_blocks_acceptance(self):
        suites = [
            {**self.data["suites"][0], "passed": 59, "failed": 1},
            self.data["suites"][1],
        ]

        result = MODULE.evaluate_test_acceptance({**self.data, "suites": suites})

        self.assertIn("failed tests present: 1", result["blocking_findings"])

    def test_open_high_defect_blocks_acceptance(self):
        defect = {
            "defect_id": "BUG-1",
            "severity": "high",
            "status": "open",
            "evidence_reference": "ISSUE-1",
        }

        result = MODULE.evaluate_test_acceptance({**self.data, "defects": [defect]})

        self.assertIn("open high defect: BUG-1", result["blocking_findings"])

    def test_missed_pass_and_coverage_thresholds_are_reported(self):
        data = {
            **self.data,
            "minimum_pass_rate_percent": "99",
            "minimum_coverage_percent": "90",
        }

        result = MODULE.evaluate_test_acceptance(data)

        self.assertIn("pass rate below threshold: 98.00 < 99.00", result["blocking_findings"])
        self.assertIn("coverage below threshold: 85.00 < 90.00", result["blocking_findings"])


if __name__ == "__main__":
    unittest.main()
