#!/usr/bin/env python3

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "finance-accounting"
    / "scripts"
    / "validate_journal.py"
)
SPEC = spec_from_file_location("validate_journal", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class JournalValidationTests(unittest.TestCase):
    def setUp(self):
        self.entry = {
            "journal_id": "J-1",
            "period": "2026-07",
            "period_status": "open",
            "currency": "CNY",
            "source_reference": "PAY-1",
            "lines": [
                {
                    "account_code": "6401",
                    "debit": "106.00",
                    "credit": "0.00",
                    "currency": "CNY",
                },
                {
                    "account_code": "1002",
                    "debit": "0.00",
                    "credit": "106.00",
                    "currency": "CNY",
                },
            ],
        }

    def test_balanced_entry_returns_draft_posting_status(self):
        result = MODULE.validate_journal(self.entry)

        self.assertEqual(result["debit_total"], "106.00")
        self.assertEqual(result["credit_total"], "106.00")
        self.assertTrue(result["balanced"])
        self.assertEqual(result["validation_status"], "passed")
        self.assertEqual(result["posting_status"], "draft")
        self.assertEqual(result["decision_status"], "human_approval_required")

    def test_unbalanced_entry_is_rejected(self):
        entry = deepcopy(self.entry)
        entry["lines"][1]["credit"] = "105.00"

        with self.assertRaisesRegex(ValueError, "journal is not balanced"):
            MODULE.validate_journal(entry)

    def test_negative_amount_is_rejected(self):
        entry = deepcopy(self.entry)
        entry["lines"][0]["debit"] = "-1.00"

        with self.assertRaisesRegex(ValueError, "line 1 debit must be non-negative"):
            MODULE.validate_journal(entry)

    def test_line_with_both_debit_and_credit_is_rejected(self):
        entry = deepcopy(self.entry)
        entry["lines"][0]["credit"] = "1.00"

        with self.assertRaisesRegex(ValueError, "line 1 must have exactly one positive side"):
            MODULE.validate_journal(entry)

    def test_mixed_currency_is_rejected(self):
        entry = deepcopy(self.entry)
        entry["lines"][1]["currency"] = "USD"

        with self.assertRaisesRegex(ValueError, "line 2 currency must match journal currency"):
            MODULE.validate_journal(entry)

    def test_missing_source_reference_is_rejected(self):
        entry = deepcopy(self.entry)
        entry["source_reference"] = ""

        with self.assertRaisesRegex(ValueError, "missing journal fields: source_reference"):
            MODULE.validate_journal(entry)

    def test_closed_period_is_rejected(self):
        entry = deepcopy(self.entry)
        entry["period_status"] = "closed"

        with self.assertRaisesRegex(ValueError, "journal period must be open"):
            MODULE.validate_journal(entry)


if __name__ == "__main__":
    unittest.main()
