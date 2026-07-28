#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
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
            "source_reference": "QUOTE-B.pdf",
        }

    def test_normalizes_and_commercially_ranks_eligible_quotes(self):
        result = MODULE.compare_quotes(
            self.requirement, [self.quote_a, self.quote_b]
        )

        rows = {row["quote_id"]: row for row in result["quotes"]}
        self.assertEqual(rows["Q-A"]["total_price"], "200.00")
        self.assertEqual(rows["Q-A"]["commercial_rank"], 1)
        self.assertEqual(rows["Q-B"]["total_price"], "250.00")
        self.assertEqual(rows["Q-B"]["commercial_rank"], 2)
        self.assertNotIn("weighted_score", rows["Q-A"])
        self.assertNotIn("dimension_scores", rows["Q-A"])
        self.assertEqual(result["decision_status"], "human_review_required")

    def test_keeps_missing_mandatory_item_as_ineligible(self):
        incomplete = {
            **self.quote_a,
            "quote_id": "Q-MISSING",
            "items": [{"item_id": "DOCK", "quantity": "2", "unit_price": "10"}],
        }

        row = MODULE.compare_quotes(self.requirement, [incomplete])["quotes"][0]

        self.assertFalse(row["eligible"])
        self.assertIsNone(row["commercial_rank"])
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

    def test_normalizes_discount_tax_and_freight(self):
        commercial = {
            **self.quote_a,
            "discount": "10.00",
            "tax": "12.00",
            "freight": "8.00",
        }

        row = MODULE.compare_quotes(self.requirement, [commercial])["quotes"][0]

        self.assertEqual(row["line_subtotal"], "200.00")
        self.assertEqual(row["total_price"], "210.00")

    def test_requires_quote_source_but_not_quality_scoring(self):
        unsupported = {**self.quote_a, "source_reference": ""}

        row = MODULE.compare_quotes(self.requirement, [unsupported])["quotes"][0]

        self.assertFalse(row["eligible"])
        self.assertIn("missing quote source reference", row["blocking_findings"])

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
