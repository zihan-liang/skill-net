#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "procurement-supplier-database"
    / "scripts"
    / "supplier_db.py"
)
SPEC = spec_from_file_location("supplier_db", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class SupplierDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        self.connection = MODULE.connect_database(self.temp.name)
        MODULE.initialize_database(self.connection)
        self.audit = {
            "actor": "procurement-demo",
            "business_purpose": "SkillNet procurement workflow test",
            "evidence_reference": "TEST-EVIDENCE-1",
            "confirmed": True,
        }

    def tearDown(self):
        self.connection.close()
        self.temp.close()

    def upsert(self, entity_type, data, **overrides):
        return MODULE.upsert_record(
            self.connection,
            entity_type,
            data,
            **{**self.audit, **overrides},
        )

    def supplier(self, supplier_id="SUP-1", registration_id="REG-1"):
        return {
            "supplier_id": supplier_id,
            "legal_name": f"Supplier {supplier_id}",
            "registration_id": registration_id,
            "country": "CN",
            "status": "active",
        }

    def seed_supplier(self):
        self.upsert("supplier", self.supplier())

    def test_initializes_all_supplier_tables(self):
        rows = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        names = {row[0] for row in rows}

        self.assertTrue(
            {
                "suppliers",
                "qualifications",
                "offerings",
                "quotes",
                "contracts",
                "deliveries",
                "evaluations",
                "audit_log",
            }
            <= names
        )

    def test_records_every_supported_entity_with_audit_events(self):
        fixtures = [
            ("supplier", self.supplier()),
            (
                "qualification",
                {
                    "qualification_id": "QUAL-1",
                    "supplier_id": "SUP-1",
                    "qualification_type": "manufacturer_authorization",
                    "issuer": "Example Manufacturer",
                    "valid_from": "2026-01-01",
                    "valid_until": "2026-12-31",
                    "status": "valid",
                    "document_reference": "DOC-QUAL-1",
                },
            ),
            (
                "offering",
                {
                    "offering_id": "OFF-1",
                    "supplier_id": "SUP-1",
                    "category": "IT hardware",
                    "description": "Developer laptops and warranty",
                    "status": "active",
                },
            ),
            (
                "quote",
                {
                    "quote_id": "Q-1",
                    "supplier_id": "SUP-1",
                    "rfq_id": "RFQ-1",
                    "amount": "200.00",
                    "currency": "CNY",
                    "valid_until": "2026-08-31",
                    "status": "received",
                    "source_reference": "DOC-Q-1",
                },
            ),
            (
                "contract",
                {
                    "contract_id": "CON-1",
                    "supplier_id": "SUP-1",
                    "order_id": "PO-1",
                    "amount": "200.00",
                    "currency": "CNY",
                    "effective_date": "2026-07-28",
                    "end_date": "2027-07-27",
                    "status": "active",
                    "document_reference": "DOC-CON-1",
                },
            ),
            (
                "delivery",
                {
                    "delivery_id": "DEL-1",
                    "supplier_id": "SUP-1",
                    "contract_id": "CON-1",
                    "delivered_on": "2026-08-15",
                    "status": "delivered",
                    "acceptance_status": "accepted",
                    "evidence_reference": "DOC-DEL-1",
                },
            ),
            (
                "evaluation",
                {
                    "evaluation_id": "EVAL-1",
                    "supplier_id": "SUP-1",
                    "period": "2026-Q3",
                    "score": "4.20",
                    "evidence_coverage_percent": "100.00",
                    "status": "approved",
                    "evidence_reference": "DOC-EVAL-1",
                },
            ),
        ]

        results = [self.upsert(entity_type, data) for entity_type, data in fixtures]
        count = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        self.assertEqual(count, 7)
        self.assertTrue(all(isinstance(row["audit_event_id"], int) for row in results))

    def test_requires_explicit_human_confirmation(self):
        with self.assertRaisesRegex(ValueError, "human confirmation required"):
            self.upsert("supplier", self.supplier(), confirmed=False)

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], 0)

    def test_duplicate_registration_rolls_back_without_audit(self):
        self.upsert("supplier", self.supplier())

        with self.assertRaisesRegex(ValueError, "duplicate supplier registration_id"):
            self.upsert("supplier", self.supplier("SUP-2", " reg-1 "))

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], 1)

    def test_invalid_amount_and_score_do_not_mutate_database(self):
        self.seed_supplier()
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        with self.assertRaisesRegex(ValueError, "amount must be positive"):
            self.upsert(
                "quote",
                {
                    "quote_id": "Q-BAD",
                    "supplier_id": "SUP-1",
                    "rfq_id": "RFQ-1",
                    "amount": "0",
                    "currency": "CNY",
                    "valid_until": "2026-08-31",
                    "status": "received",
                    "source_reference": "BAD",
                },
            )
        with self.assertRaisesRegex(ValueError, "score must be between 0 and 5"):
            self.upsert(
                "evaluation",
                {
                    "evaluation_id": "E-BAD",
                    "supplier_id": "SUP-1",
                    "period": "2026-Q3",
                    "score": "6",
                    "evidence_coverage_percent": "100",
                    "status": "draft",
                    "evidence_reference": "BAD",
                },
            )

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM quotes").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_delivery_supplier_must_match_contract(self):
        self.upsert("supplier", self.supplier())
        self.upsert("supplier", self.supplier("SUP-2", "REG-2"))
        self.upsert(
            "contract",
            {
                "contract_id": "CON-1",
                "supplier_id": "SUP-1",
                "order_id": "PO-1",
                "amount": "200",
                "currency": "CNY",
                "effective_date": "2026-07-28",
                "end_date": "2027-07-27",
                "status": "active",
                "document_reference": "DOC-CON-1",
            },
        )
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        with self.assertRaisesRegex(ValueError, "delivery supplier must match contract"):
            self.upsert(
                "delivery",
                {
                    "delivery_id": "DEL-BAD",
                    "supplier_id": "SUP-2",
                    "contract_id": "CON-1",
                    "delivered_on": "2026-08-15",
                    "status": "delivered",
                    "acceptance_status": "pending_review",
                    "evidence_reference": "DOC-DEL-BAD",
                },
            )

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_query_returns_only_requested_allowed_fields(self):
        self.seed_supplier()

        result = MODULE.query_record(
            self.connection,
            "supplier",
            "SUP-1",
            ["supplier_id", "legal_name", "status"],
        )

        self.assertEqual(
            result,
            {
                "supplier_id": "SUP-1",
                "legal_name": "Supplier SUP-1",
                "status": "active",
            },
        )
        with self.assertRaisesRegex(ValueError, "unsupported query fields"):
            MODULE.query_record(
                self.connection, "supplier", "SUP-1", ["registration_id", "secret"]
            )

    def test_update_audit_contains_before_and_after_values(self):
        self.seed_supplier()
        self.upsert("supplier", {**self.supplier(), "status": "suspended"})

        row = self.connection.execute(
            "SELECT action, before_json, after_json FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()

        self.assertEqual(row["action"], "update")
        self.assertEqual(json.loads(row["before_json"])["status"], "active")
        self.assertEqual(json.loads(row["after_json"])["status"], "suspended")


if __name__ == "__main__":
    unittest.main()
