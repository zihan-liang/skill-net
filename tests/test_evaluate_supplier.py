#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "procurement-supplier-evaluation"
    / "scripts"
    / "evaluate_supplier.py"
)
SPEC = spec_from_file_location("evaluate_supplier", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SupplierEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "evaluation_id": "EVAL-1",
            "supplier_id": "SUP-1",
            "period": "2026-Q3",
            "dimensions": {
                "delivery": {"score": "4", "evidence_reference": "DEL-1"},
                "quality": {"score": "5", "evidence_reference": "QA-1"},
                "service": {"score": "3", "evidence_reference": "SRV-1"},
                "commercial_performance": {
                    "score": "4",
                    "evidence_reference": "COM-1",
                },
                "compliance": {"score": "5", "evidence_reference": "CMP-1"},
            },
        }

    def test_calculates_hand_checked_complete_score(self):
        result = MODULE.evaluate_supplier(self.data)

        self.assertEqual(result["weighted_score"], "4.20")
        self.assertEqual(result["evidence_coverage_percent"], "100.00")
        self.assertEqual(result["performance_band"], "strong")
        self.assertEqual(result["missing_evidence"], [])
        self.assertEqual(result["decision_status"], "human_review_required")

    def test_renormalizes_score_and_reports_partial_coverage(self):
        data = {
            **self.data,
            "dimensions": {
                "delivery": {"score": "5", "evidence_reference": "DEL-1"},
                "quality": {"score": "4", "evidence_reference": "QA-1"},
            },
        }

        result = MODULE.evaluate_supplier(data)

        self.assertEqual(result["weighted_score"], "4.45")
        self.assertEqual(result["evidence_coverage_percent"], "55.00")
        self.assertEqual(
            result["missing_evidence"],
            ["commercial_performance", "compliance", "service"],
        )

    def test_excludes_score_without_evidence(self):
        data = {
            **self.data,
            "dimensions": {
                "quality": {"score": "5", "evidence_reference": ""},
            },
        }

        result = MODULE.evaluate_supplier(data)

        self.assertIsNone(result["weighted_score"])
        self.assertEqual(result["evidence_coverage_percent"], "0.00")
        self.assertEqual(result["performance_band"], "insufficient_evidence")
        self.assertIn("quality", result["missing_evidence"])

    def test_rejects_score_outside_zero_to_five(self):
        data = {
            **self.data,
            "dimensions": {
                **self.data["dimensions"],
                "quality": {"score": "6", "evidence_reference": "QA-1"},
            },
        }

        with self.assertRaisesRegex(ValueError, "quality score must be between 0 and 5"):
            MODULE.evaluate_supplier(data)

    def test_rejects_weights_that_do_not_sum_to_one(self):
        data = {
            **self.data,
            "weights": {
                "delivery": "0.25",
                "quality": "0.30",
                "service": "0.20",
                "commercial_performance": "0.15",
                "compliance": "0.20",
            },
        }

        with self.assertRaisesRegex(ValueError, "weights must sum to 1"):
            MODULE.evaluate_supplier(data)

    def test_rejects_unknown_dimension(self):
        data = {
            **self.data,
            "dimensions": {
                **self.data["dimensions"],
                "personal_friendship": {"score": "5", "evidence_reference": "X"},
            },
        }

        with self.assertRaisesRegex(ValueError, "unsupported dimensions"):
            MODULE.evaluate_supplier(data)


if __name__ == "__main__":
    unittest.main()
