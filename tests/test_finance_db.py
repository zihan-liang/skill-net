#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "finance-database"
    / "scripts"
    / "finance_db.py"
)
SPEC = spec_from_file_location("finance_db", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class FinanceDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        self.connection = MODULE.connect_database(self.temp.name)
        MODULE.initialize_database(self.connection)
        self.audit = {
            "actor": "finance-demo",
            "business_purpose": "SkillNet finance workflow test",
            "evidence_reference": "TEST-EVIDENCE-1",
        }

    def tearDown(self):
        self.connection.close()
        self.temp.close()

    def upsert(self, entity_type, data):
        return MODULE.upsert_record(
            self.connection,
            entity_type,
            data,
            **self.audit,
        )

    def seed_department(self):
        self.upsert(
            "department",
            {"department_id": "D-1", "name": "Product", "status": "active"},
        )

    def test_initializes_all_finance_tables(self):
        rows = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        names = {row[0] for row in rows}

        self.assertTrue(
            {
                "departments",
                "budgets",
                "transactions",
                "invoices",
                "payments",
                "open_items",
                "report_snapshots",
                "audit_log",
            }
            <= names
        )

    def test_records_every_supported_entity_with_audit_events(self):
        fixtures = [
            (
                "department",
                {"department_id": "D-1", "name": "Product", "status": "active"},
            ),
            (
                "budget",
                {
                    "budget_id": "B-1",
                    "department_id": "D-1",
                    "period": "2026-Q3",
                    "currency": "CNY",
                    "amount": "1000.00",
                    "status": "approved",
                },
            ),
            (
                "transaction",
                {
                    "transaction_id": "T-1",
                    "department_id": "D-1",
                    "kind": "expense",
                    "amount": "106.00",
                    "currency": "CNY",
                    "occurred_on": "2026-07-28",
                    "status": "posted",
                    "source_reference": "J-1",
                },
            ),
            (
                "invoice",
                {
                    "invoice_id": "INV-1",
                    "supplier_id": "SUP-1",
                    "invoice_number": "2026-001",
                    "amount": "106.00",
                    "currency": "CNY",
                    "status": "verified",
                },
            ),
            (
                "payment",
                {
                    "payment_id": "P-1",
                    "invoice_id": "INV-1",
                    "payee_id": "SUP-1",
                    "amount": "106.00",
                    "currency": "CNY",
                    "status": "approved",
                },
            ),
            (
                "open_item",
                {
                    "item_id": "AR-1",
                    "kind": "receivable",
                    "counterparty_id": "CUS-1",
                    "amount": "200.00",
                    "currency": "CNY",
                    "due_date": "2026-08-31",
                    "status": "open",
                },
            ),
            (
                "report_snapshot",
                {
                    "report_id": "RPT-1",
                    "period": "2026-07",
                    "currency": "CNY",
                    "status": "approved",
                    "payload": {"income_total": "600.00"},
                },
            ),
        ]

        results = [self.upsert(entity_type, data) for entity_type, data in fixtures]
        audit_count = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        self.assertTrue(all(isinstance(result["audit_event_id"], int) for result in results))
        self.assertEqual(audit_count, 7)

    def test_duplicate_invoice_key_rolls_back_without_audit(self):
        first = {
            "invoice_id": "INV-1",
            "supplier_id": "SUP-1",
            "invoice_number": "2026-001",
            "amount": "106.00",
            "currency": "CNY",
            "status": "verified",
        }
        second = {**first, "invoice_id": "INV-2"}
        self.upsert("invoice", first)

        with self.assertRaisesRegex(ValueError, "duplicate invoice key"):
            self.upsert("invoice", second)

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM invoices").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], 1)

    def test_invalid_records_do_not_mutate_database(self):
        self.seed_department()
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        with self.assertRaisesRegex(ValueError, "amount must be non-negative"):
            self.upsert(
                "budget",
                {
                    "budget_id": "B-BAD",
                    "department_id": "D-1",
                    "period": "2026-Q3",
                    "currency": "CNY",
                    "amount": "-1.00",
                    "status": "draft",
                },
            )
        with self.assertRaisesRegex(ValueError, "unsupported transaction kind"):
            self.upsert(
                "transaction",
                {
                    "transaction_id": "T-BAD",
                    "department_id": "D-1",
                    "kind": "transfer",
                    "amount": "1.00",
                    "currency": "CNY",
                    "occurred_on": "2026-07-28",
                    "status": "draft",
                    "source_reference": "BAD",
                },
            )
        with self.assertRaisesRegex(ValueError, "currency must be a three-letter code"):
            self.upsert(
                "open_item",
                {
                    "item_id": "AR-BAD",
                    "kind": "receivable",
                    "counterparty_id": "CUS-1",
                    "amount": "1.00",
                    "currency": "CN",
                    "due_date": "2026-08-31",
                    "status": "open",
                },
            )

        audit_after = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        self.assertEqual(audit_after, audit_before)

    def test_query_returns_only_requested_allowed_fields(self):
        self.seed_department()
        self.upsert(
            "budget",
            {
                "budget_id": "B-1",
                "department_id": "D-1",
                "period": "2026-Q3",
                "currency": "CNY",
                "amount": "1000.00",
                "status": "approved",
            },
        )

        result = MODULE.query_record(
            self.connection,
            "budget",
            "B-1",
            ["amount", "status"],
        )

        self.assertEqual(result, {"amount": "1000.00", "status": "approved"})
        with self.assertRaisesRegex(ValueError, "unsupported query fields"):
            MODULE.query_record(self.connection, "budget", "B-1", ["not_a_field"])

    def test_update_audit_contains_before_and_after_values(self):
        self.seed_department()
        budget = {
            "budget_id": "B-1",
            "department_id": "D-1",
            "period": "2026-Q3",
            "currency": "CNY",
            "amount": "1000.00",
            "status": "draft",
        }
        self.upsert("budget", budget)
        self.upsert("budget", {**budget, "status": "approved"})
        row = self.connection.execute(
            "SELECT before_json, after_json, actor, business_purpose, evidence_reference "
            "FROM audit_log WHERE entity_type = 'budget' ORDER BY id DESC LIMIT 1"
        ).fetchone()

        self.assertEqual(json.loads(row["before_json"])["status"], "draft")
        self.assertEqual(json.loads(row["after_json"])["status"], "approved")
        self.assertEqual(row["actor"], "finance-demo")
        self.assertEqual(row["business_purpose"], "SkillNet finance workflow test")
        self.assertEqual(row["evidence_reference"], "TEST-EVIDENCE-1")


if __name__ == "__main__":
    unittest.main()
