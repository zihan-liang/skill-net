#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "business-opportunity-assessment"
    / "scripts"
    / "evaluate_opportunity.py"
)
SPEC = spec_from_file_location("evaluate_opportunity", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class OpportunityEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "customer_id": "CUS-1",
            "opportunity_id": "OPP-1",
            "dimensions": {
                "strategic_fit": {"score": "5", "evidence_reference": "E-STRATEGY"},
                "need_clarity": {"score": "4", "evidence_reference": "E-NEED"},
                "authority_access": {"score": "3", "evidence_reference": "E-AUTH"},
                "budget_readiness": {"score": "2", "evidence_reference": "E-BUDGET"},
                "timeline_readiness": {"score": "4", "evidence_reference": "E-TIME"},
                "delivery_fit": {"score": "5", "evidence_reference": "E-DELIVERY"},
            },
            "risks": [],
        }

    def test_returns_hand_checked_weighted_score_and_human_review(self):
        result = MODULE.evaluate_opportunity(self.data)

        self.assertEqual(result["weighted_score_out_of_5"], "3.95")
        self.assertEqual(result["evidence_coverage_percent"], "100.00")
        self.assertTrue(result["automated_readiness_passed"])
        self.assertEqual(result["decision_status"], "human_review_required")

    def test_accepts_complete_custom_weights(self):
        weights = {
            "strategic_fit": "0.10",
            "need_clarity": "0.10",
            "authority_access": "0.20",
            "budget_readiness": "0.20",
            "timeline_readiness": "0.20",
            "delivery_fit": "0.20",
        }

        result = MODULE.evaluate_opportunity({**self.data, "weights": weights})

        self.assertEqual(result["weighted_score_out_of_5"], "3.70")

    def test_missing_evidence_blocks_readiness_and_reduces_coverage(self):
        dimensions = {
            **self.data["dimensions"],
            "budget_readiness": {"score": "2", "evidence_reference": ""},
        }

        result = MODULE.evaluate_opportunity({**self.data, "dimensions": dimensions})

        self.assertFalse(result["automated_readiness_passed"])
        self.assertEqual(result["evidence_coverage_percent"], "83.33")
        self.assertIn("missing evidence for dimension: budget_readiness", result["blocking_findings"])
        self.assertEqual(result["decision_status"], "blocked")

    def test_rejects_missing_dimension(self):
        dimensions = dict(self.data["dimensions"])
        dimensions.pop("delivery_fit")

        with self.assertRaisesRegex(ValueError, "dimensions must match required set"):
            MODULE.evaluate_opportunity({**self.data, "dimensions": dimensions})

    def test_rejects_out_of_range_score(self):
        dimensions = {
            **self.data["dimensions"],
            "delivery_fit": {"score": "6", "evidence_reference": "E-DELIVERY"},
        }

        with self.assertRaisesRegex(ValueError, "score must be between 0 and 5"):
            MODULE.evaluate_opportunity({**self.data, "dimensions": dimensions})

    def test_rejects_invalid_weight_keys_or_sum(self):
        with self.assertRaisesRegex(ValueError, "weights must match required set"):
            MODULE.evaluate_opportunity({**self.data, "weights": {"strategic_fit": "1"}})

        weights = {name: "0.10" for name in self.data["dimensions"]}
        with self.assertRaisesRegex(ValueError, "weights must sum to 1"):
            MODULE.evaluate_opportunity({**self.data, "weights": weights})

    def test_open_critical_risk_blocks_readiness(self):
        risk = {
            "risk_id": "RISK-1",
            "severity": "critical",
            "status": "open",
            "evidence_reference": "E-RISK-1",
        }

        result = MODULE.evaluate_opportunity({**self.data, "risks": [risk]})

        self.assertFalse(result["automated_readiness_passed"])
        self.assertIn("open critical risk: RISK-1", result["blocking_findings"])
        self.assertEqual(result["decision_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
