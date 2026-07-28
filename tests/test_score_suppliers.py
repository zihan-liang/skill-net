#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "procurement-supplier-scoring"
    / "scripts"
    / "score_suppliers.py"
)
SPEC = spec_from_file_location("score_suppliers", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SupplierScoringTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "scoring_id": "SCORE-1",
            "request_id": "REQ-1",
            "rfq_id": "RFQ-1",
            "weights": {
                "qualification": "0.20",
                "price": "0.30",
                "delivery": "0.20",
                "quality": "0.20",
                "risk": "0.10",
            },
            "suppliers": [
                {
                    "supplier_id": "SUP-A",
                    "qualification": {"score": "5", "evidence_reference": "QUAL-A"},
                    "price": {"score": "4", "evidence_reference": "QUOTE-A"},
                    "delivery": {"score": "3", "evidence_reference": "DEL-A"},
                    "quality": {"score": "4", "evidence_reference": "QA-A"},
                    "risk": {"score": "2", "evidence_reference": "RISK-A"},
                },
                {
                    "supplier_id": "SUP-B",
                    "qualification": {"score": "4", "evidence_reference": "QUAL-B"},
                    "price": {"score": "5", "evidence_reference": "QUOTE-B"},
                    "delivery": {"score": "4", "evidence_reference": "DEL-B"},
                    "quality": {"score": "3", "evidence_reference": "QA-B"},
                    "risk": {"score": "4", "evidence_reference": "RISK-B"},
                },
            ],
        }

    def test_calculates_evidence_backed_scores_and_ranking(self):
        result = MODULE.score_suppliers(self.data)

        rows = {row["supplier_id"]: row for row in result["suppliers"]}
        self.assertEqual(rows["SUP-A"]["weighted_score"], "3.80")
        self.assertEqual(rows["SUP-A"]["rank"], 2)
        self.assertEqual(rows["SUP-B"]["weighted_score"], "4.10")
        self.assertEqual(rows["SUP-B"]["rank"], 1)
        self.assertEqual(result["decision_status"], "human_review_required")

    def test_missing_evidence_blocks_ranking(self):
        self.data["suppliers"][0]["quality"]["evidence_reference"] = ""

        row = MODULE.score_suppliers(self.data)["suppliers"][0]

        self.assertFalse(row["eligible"])
        self.assertIsNone(row["rank"])
        self.assertIn("missing quality evidence", row["blocking_findings"])

    def test_rejects_weights_not_equal_to_one(self):
        self.data["weights"]["risk"] = "0.20"

        with self.assertRaisesRegex(ValueError, "weights must sum to 1"):
            MODULE.score_suppliers(self.data)

    def test_rejects_score_outside_zero_to_five(self):
        self.data["suppliers"][0]["risk"]["score"] = "6"

        with self.assertRaisesRegex(ValueError, "risk score must be between 0 and 5"):
            MODULE.score_suppliers(self.data)

    def test_rejects_duplicate_supplier_ids(self):
        self.data["suppliers"][1]["supplier_id"] = "SUP-A"

        with self.assertRaisesRegex(ValueError, "duplicate supplier_id"):
            MODULE.score_suppliers(self.data)


if __name__ == "__main__":
    unittest.main()
