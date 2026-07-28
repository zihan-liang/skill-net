#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "business-solution-quotation"
    / "scripts"
    / "calculate_quotation.py"
)
SPEC = spec_from_file_location("calculate_quotation", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class QuotationCalculationTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "quotation_id": "QUOTE-1",
            "customer_id": "CUS-1",
            "opportunity_id": "OPP-1",
            "solution_id": "SOL-1",
            "currency": "CNY",
            "issue_date": "2026-07-28",
            "valid_until": "2026-08-28",
            "evidence_reference": "REQ-CONFIRMED-1",
            "discount_percent": "10",
            "tax_rate_percent": "6",
            "lines": [
                {
                    "line_id": "L1",
                    "description": "Platform configuration",
                    "quantity": "2",
                    "unit_price": "99.95",
                },
                {
                    "line_id": "L2",
                    "description": "Training session",
                    "quantity": "1",
                    "unit_price": "50.10",
                },
            ],
        }

    def test_returns_hand_checked_decimal_totals_as_draft(self):
        result = MODULE.calculate_quotation(self.data)

        self.assertEqual(result["subtotal"], "250.00")
        self.assertEqual(result["discount_amount"], "25.00")
        self.assertEqual(result["taxable_amount"], "225.00")
        self.assertEqual(result["tax_amount"], "13.50")
        self.assertEqual(result["total"], "238.50")
        self.assertEqual(result["quotation_status"], "draft_human_review_required")
        self.assertEqual(result["external_action"], "not_performed")

    def test_rejects_duplicate_line_ids(self):
        lines = [self.data["lines"][0], {**self.data["lines"][1], "line_id": "L1"}]

        with self.assertRaisesRegex(ValueError, "duplicate line_id: L1"):
            MODULE.calculate_quotation({**self.data, "lines": lines})

    def test_rejects_non_positive_quantity_and_negative_price(self):
        with self.assertRaisesRegex(ValueError, "quantity must be positive"):
            MODULE.calculate_quotation(
                {**self.data, "lines": [{**self.data["lines"][0], "quantity": "0"}]}
            )
        with self.assertRaisesRegex(ValueError, "unit_price must be non-negative"):
            MODULE.calculate_quotation(
                {**self.data, "lines": [{**self.data["lines"][0], "unit_price": "-1"}]}
            )

    def test_rejects_invalid_discount_or_tax_rate(self):
        with self.assertRaisesRegex(ValueError, "discount_percent must be between 0 and 100"):
            MODULE.calculate_quotation({**self.data, "discount_percent": "101"})
        with self.assertRaisesRegex(ValueError, "tax_rate_percent must be between 0 and 100"):
            MODULE.calculate_quotation({**self.data, "tax_rate_percent": "-1"})

    def test_rejects_invalid_currency(self):
        with self.assertRaisesRegex(ValueError, "currency must be a three-letter code"):
            MODULE.calculate_quotation({**self.data, "currency": "RMB" + "1"})

    def test_rejects_invalid_or_reversed_validity_dates(self):
        with self.assertRaisesRegex(ValueError, "issue_date must be ISO date"):
            MODULE.calculate_quotation({**self.data, "issue_date": "28/07/2026"})
        with self.assertRaisesRegex(ValueError, "valid_until must not precede issue_date"):
            MODULE.calculate_quotation({**self.data, "valid_until": "2026-07-27"})

    def test_requires_source_evidence_and_non_empty_lines(self):
        with self.assertRaisesRegex(ValueError, "missing required fields: evidence_reference"):
            MODULE.calculate_quotation({**self.data, "evidence_reference": ""})
        with self.assertRaisesRegex(ValueError, "lines must be a non-empty list"):
            MODULE.calculate_quotation({**self.data, "lines": []})


if __name__ == "__main__":
    unittest.main()
