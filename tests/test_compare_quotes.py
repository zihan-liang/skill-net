#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "procurement-quote-comparison"
    / "scripts"
    / "compare_quotes.py"
)
SPEC = spec_from_file_location("compare_quotes", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class QuoteComparisonTests(unittest.TestCase):
    def setUp(self):
        self.requirement = {
            "request_id": "REQ-1",
            "rfq_id": "RFQ-1",
            "currency": "CNY",
            "comparison_date": "2026-07-28",
            "required_items": [{"item_id": "LAPTOP", "quantity": "2"}],
        }
        self.quote_a = {
            "quote_id": "Q-A",
            "supplier_id": "SUP-A",
            "currency": "CNY",
            "valid_until": "2026-08-31",
            "items": [
                {"item_id": "LAPTOP", "quantity": "2", "unit_price": "100.00"}
            ],
            "delivery_days": "10",
            "quality_score": "4",
            "quality_evidence": "QA-A",
            "service_score": "5",
            "service_evidence": "SRV-A",
            "source_reference": "QUOTE-A.pdf",
        }
        self.quote_b = {
            "quote_id": "Q-B",
            "supplier_id": "SUP-B",
            "currency": "CNY",
            "valid_until": "2026-08-31",
            "items": [
                {"item_id": "LAPTOP", "quantity": "2", "unit_price": "125.00"}
            ],
            "delivery_days": "5",
            "quality_score": "5",
            "quality_evidence": "QA-B",
            "service_score": "4",
            "service_evidence": "SRV-B",
            "source_reference": "QUOTE-B.pdf",
        }

    def test_ranks_eligible_quotes_with_hand_checked_scores(self):
        result = MODULE.compare_quotes(
            self.requirement, [self.quote_a, self.quote_b]
        )

        rows = {row["quote_id"]: row for row in result["quotes"]}
        self.assertEqual(rows["Q-A"]["total_price"], "200.00")
        self.assertEqual(rows["Q-A"]["weighted_score"], "4.18")
        self.assertEqual(rows["Q-A"]["rank"], 2)
        self.assertEqual(rows["Q-B"]["total_price"], "250.00")
        self.assertEqual(rows["Q-B"]["weighted_score"], "4.45")
        self.assertEqual(rows["Q-B"]["rank"], 1)
        self.assertEqual(result["decision_status"], "human_review_required")

    def test_keeps_missing_mandatory_item_as_ineligible(self):
        incomplete = {
            **self.quote_a,
            "quote_id": "Q-MISSING",
            "items": [{"item_id": "DOCK", "quantity": "2", "unit_price": "10"}],
        }

        row = MODULE.compare_quotes(self.requirement, [incomplete])["quotes"][0]

        self.assertFalse(row["eligible"])
        self.assertIsNone(row["rank"])
        self.assertIn("missing mandatory item LAPTOP", row["blocking_findings"])

    def test_currency_mismatch_and_expiry_are_visible(self):
        mismatched = {
            **self.quote_a,
            "currency": "USD",
            "valid_until": "2026-07-27",
        }

        row = MODULE.compare_quotes(self.requirement, [mismatched])["quotes"][0]

        self.assertFalse(row["eligible"])
        self.assertIn("currency mismatch: USD != CNY", row["blocking_findings"])
        self.assertIn("quote expired before comparison date", row["blocking_findings"])

    def test_missing_score_evidence_makes_quote_ineligible(self):
        unsupported = {**self.quote_a, "quality_evidence": ""}

        row = MODULE.compare_quotes(self.requirement, [unsupported])["quotes"][0]

        self.assertFalse(row["eligible"])
        self.assertIn("missing quality evidence", row["blocking_findings"])

    def test_rejects_invalid_weights(self):
        requirement = {
            **self.requirement,
            "weights": {
                "price": "0.50",
                "delivery": "0.25",
                "quality": "0.20",
                "service": "0.15",
            },
        }

        with self.assertRaisesRegex(ValueError, "weights must sum to 1"):
            MODULE.compare_quotes(requirement, [self.quote_a])

    def test_rejects_duplicate_quote_ids(self):
        duplicate = {**self.quote_b, "quote_id": "Q-A"}

        with self.assertRaisesRegex(ValueError, "duplicate quote_id"):
            MODULE.compare_quotes(self.requirement, [self.quote_a, duplicate])

    def test_rejects_non_positive_price(self):
        invalid = {
            **self.quote_a,
            "items": [
                {"item_id": "LAPTOP", "quantity": "2", "unit_price": "0"}
            ],
        }

        with self.assertRaisesRegex(ValueError, "unit_price must be positive"):
            MODULE.compare_quotes(self.requirement, [invalid])


if __name__ == "__main__":
    unittest.main()
