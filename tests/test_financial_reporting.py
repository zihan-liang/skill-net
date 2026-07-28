#!/usr/bin/env python3

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "finance-reporting"
    / "scripts"
    / "generate_financial_report.py"
)
SPEC = spec_from_file_location("generate_financial_report", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class FinancialReportingTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "report_id": "RPT-1",
            "period": "2026-07",
            "currency": "CNY",
            "opening_cash": "100.00",
            "closing_cash": "300.00",
            "budgets": [
                {
                    "budget_id": "B-1",
                    "amount": "1000.00",
                    "currency": "CNY",
                    "status": "approved",
                    "source_reference": "BUDGET-APPROVAL-1",
                },
                {
                    "budget_id": "B-2",
                    "amount": "500.00",
                    "currency": "CNY",
                    "status": "draft",
                    "source_reference": "DRAFT-2",
                },
            ],
            "transactions": [
                {
                    "transaction_id": "T-1",
                    "kind": "income",
                    "amount": "600.00",
                    "currency": "CNY",
                    "status": "posted",
                    "source_reference": "J-1",
                },
                {
                    "transaction_id": "T-2",
                    "kind": "expense",
                    "amount": "400.00",
                    "currency": "CNY",
                    "status": "paid",
                    "source_reference": "J-2",
                },
                {
                    "transaction_id": "T-3",
                    "kind": "expense",
                    "amount": "50.00",
                    "currency": "CNY",
                    "status": "draft",
                    "source_reference": "DRAFT-3",
                },
            ],
            "receivables": [
                {
                    "item_id": "AR-1",
                    "amount": "200.00",
                    "currency": "CNY",
                    "status": "open",
                    "source_reference": "AR-SOURCE-1",
                },
                {
                    "item_id": "AR-2",
                    "amount": "100.00",
                    "currency": "CNY",
                    "status": "closed",
                    "source_reference": "AR-SOURCE-2",
                },
            ],
            "payables": [
                {
                    "item_id": "AP-1",
                    "amount": "150.00",
                    "currency": "CNY",
                    "status": "overdue",
                    "source_reference": "AP-SOURCE-1",
                },
                {
                    "item_id": "AP-2",
                    "amount": "50.00",
                    "currency": "CNY",
                    "status": "paid",
                    "source_reference": "AP-SOURCE-2",
                },
            ],
        }

    def test_generates_hand_checked_reconciled_summary(self):
        result = MODULE.generate_report(self.data)

        self.assertEqual(result["budget_total"], "1000.00")
        self.assertEqual(result["expense_actual"], "400.00")
        self.assertEqual(result["budget_variance"], "600.00")
        self.assertEqual(result["income_total"], "600.00")
        self.assertEqual(result["expense_total"], "400.00")
        self.assertEqual(result["net_movement"], "200.00")
        self.assertEqual(result["expected_closing_cash"], "300.00")
        self.assertEqual(result["reconciliation_difference"], "0.00")
        self.assertEqual(result["receivables_total"], "200.00")
        self.assertEqual(result["payables_total"], "150.00")
        self.assertEqual(result["evidence_coverage"], 1.0)
        self.assertEqual(result["report_status"], "ready_for_review")

    def test_unreconciled_cash_keeps_report_draft(self):
        data = deepcopy(self.data)
        data["closing_cash"] = "290.00"

        result = MODULE.generate_report(data)

        self.assertEqual(result["reconciliation_difference"], "-10.00")
        self.assertEqual(result["report_status"], "draft_unreconciled")

    def test_missing_source_keeps_report_incomplete(self):
        data = deepcopy(self.data)
        data["transactions"][0]["source_reference"] = ""

        result = MODULE.generate_report(data)

        self.assertEqual(result["evidence_coverage"], 0.8)
        self.assertEqual(result["report_status"], "draft_incomplete")

    def test_currency_mismatch_is_rejected(self):
        data = deepcopy(self.data)
        data["payables"][0]["currency"] = "USD"

        with self.assertRaisesRegex(ValueError, "payables item AP-1 currency must be CNY"):
            MODULE.generate_report(data)

    def test_negative_amount_is_rejected(self):
        data = deepcopy(self.data)
        data["transactions"][0]["amount"] = "-1.00"

        with self.assertRaisesRegex(ValueError, "transactions item T-1 amount must be non-negative"):
            MODULE.generate_report(data)


if __name__ == "__main__":
    unittest.main()
