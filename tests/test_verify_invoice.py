#!/usr/bin/env python3

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "finance-invoice-verification"
    / "scripts"
    / "verify_invoice.py"
)
SPEC = spec_from_file_location("verify_invoice", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class InvoiceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.invoice = {
            "invoice_id": "INV-1",
            "supplier_id": "SUP-1",
            "invoice_number": "2026-001",
            "issue_date": "2026-07-28",
            "currency": "CNY",
            "subtotal": "100.00",
            "tax": "6.00",
            "total": "106.00",
        }
        self.expense = {
            "expense_id": "EXP-1",
            "supplier_id": "SUP-1",
            "currency": "CNY",
            "amount": "106.00",
        }

    def test_matching_invoice_returns_auditable_non_authenticity_result(self):
        result = MODULE.verify_invoice(self.invoice, self.expense, [])

        self.assertEqual(result["arithmetic_status"], "passed")
        self.assertEqual(result["request_match_status"], "passed")
        self.assertEqual(result["duplicate_status"], "clear")
        self.assertEqual(result["discrepancies"], [])
        self.assertEqual(result["authenticity_status"], "not_verified")
        self.assertEqual(result["decision_status"], "human_review_required")

    def test_total_mismatch_is_reported(self):
        invoice = deepcopy(self.invoice)
        invoice["total"] = "107.00"

        result = MODULE.verify_invoice(invoice, self.expense, [])

        self.assertEqual(result["arithmetic_status"], "failed")
        self.assertIn("invoice_total_mismatch", {item["code"] for item in result["discrepancies"]})

    def test_missing_required_field_is_rejected(self):
        invoice = deepcopy(self.invoice)
        del invoice["issue_date"]

        with self.assertRaisesRegex(ValueError, "missing invoice fields: issue_date"):
            MODULE.verify_invoice(invoice, self.expense, [])

    def test_currency_and_supplier_mismatches_are_reported(self):
        expense = deepcopy(self.expense)
        expense["currency"] = "USD"
        expense["supplier_id"] = "SUP-2"

        result = MODULE.verify_invoice(self.invoice, expense, [])
        codes = {item["code"] for item in result["discrepancies"]}

        self.assertEqual(result["request_match_status"], "failed")
        self.assertTrue({"currency_mismatch", "supplier_mismatch"} <= codes)

    def test_duplicate_supplier_invoice_key_is_flagged(self):
        result = MODULE.verify_invoice(self.invoice, self.expense, ["SUP-1|2026-001"])

        self.assertEqual(result["duplicate_status"], "potential_duplicate")
        self.assertIn("duplicate_invoice_key", {item["code"] for item in result["discrepancies"]})

    def test_negative_money_is_rejected(self):
        invoice = deepcopy(self.invoice)
        invoice["tax"] = "-1.00"

        with self.assertRaisesRegex(ValueError, "tax must be non-negative"):
            MODULE.verify_invoice(invoice, self.expense, [])


if __name__ == "__main__":
    unittest.main()
