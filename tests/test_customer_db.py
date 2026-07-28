#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "business-customer-database"
    / "scripts"
    / "customer_db.py"
)
SPEC = spec_from_file_location("customer_db", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CustomerDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        self.connection = MODULE.connect_database(self.temp.name)
        MODULE.initialize_database(self.connection)
        self.audit = {
            "actor": "business-demo",
            "business_purpose": "SkillNet business workflow test",
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

    def customer(self, customer_id="CUS-1"):
        return {
            "customer_id": customer_id,
            "legal_name": f"Fictional Customer {customer_id}",
            "display_name": f"Customer {customer_id}",
            "segment": "merchant",
            "region": "Shanghai",
            "owner": "Business Team",
            "status": "active",
        }

    def contact(self, contact_id="CONT-1", customer_id="CUS-1", email="buyer@example.invalid"):
        return {
            "contact_id": contact_id,
            "customer_id": customer_id,
            "name": "Fictional Buyer",
            "role": "Business Contact",
            "business_email": email,
            "business_phone": "",
            "contact_basis": "customer-provided business contact",
            "status": "active",
        }

    def quotation(self, quotation_id="QUOTE-1", customer_id="CUS-1", number="Q-2026-001"):
        return {
            "quotation_id": quotation_id,
            "customer_id": customer_id,
            "opportunity_id": "OPP-1",
            "quotation_number": number,
            "version": "1",
            "currency": "CNY",
            "total_amount": "238.50",
            "valid_until": "2026-08-28",
            "status": "approved",
            "evidence_reference": "QUOTE-EVIDENCE-1",
        }

    def contract(self, contract_id="CON-1", customer_id="CUS-1", quotation_id="QUOTE-1", reference="CTR-2026-001"):
        return {
            "contract_id": contract_id,
            "customer_id": customer_id,
            "quotation_id": quotation_id,
            "contract_reference": reference,
            "version": "1",
            "document_digest": "sha256:" + "c" * 64,
            "status": "signed",
            "effective_date": "2026-08-01",
            "expiry_date": "2027-07-31",
            "evidence_reference": "SIGNATURE-EVIDENCE-1",
        }

    def seed_contract(self):
        self.upsert("customer", self.customer())
        self.upsert("quotation", self.quotation())
        self.upsert("contract", self.contract())

    def test_initializes_all_customer_lifecycle_tables(self):
        rows = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        names = {row[0] for row in rows}

        self.assertTrue(
            {
                "customers",
                "contacts",
                "customer_requirements",
                "communication_records",
                "quotation_records",
                "contract_records",
                "project_progress",
                "payment_records",
                "renewal_records",
                "audit_log",
            }
            <= names
        )

    def test_records_every_supported_entity_with_audit_events(self):
        fixtures = [
            ("customer", self.customer()),
            ("contact", self.contact()),
            (
                "requirement",
                {
                    "requirement_id": "REQ-1",
                    "customer_id": "CUS-1",
                    "version": "1",
                    "summary": "Merchant onboarding workflow",
                    "status": "confirmed",
                    "evidence_reference": "REQ-EVIDENCE-1",
                },
            ),
            (
                "communication",
                {
                    "communication_id": "COMM-1",
                    "customer_id": "CUS-1",
                    "contact_id": "CONT-1",
                    "requirement_id": "REQ-1",
                    "occurred_at": "2026-07-28T09:00:00+08:00",
                    "channel": "meeting",
                    "summary": "Confirmed intended outcomes and open budget question",
                    "status": "recorded",
                    "evidence_reference": "COMM-EVIDENCE-1",
                },
            ),
            ("quotation", self.quotation()),
            ("contract", self.contract()),
            (
                "project_progress",
                {
                    "progress_id": "PROGRESS-1",
                    "customer_id": "CUS-1",
                    "contract_id": "CON-1",
                    "project_id": "PROJ-1",
                    "as_of_date": "2026-08-10",
                    "completion_percent": "57.50",
                    "status": "in_progress",
                    "evidence_reference": "PROGRESS-EVIDENCE-1",
                },
            ),
            (
                "payment",
                {
                    "payment_id": "PAY-1",
                    "customer_id": "CUS-1",
                    "contract_id": "CON-1",
                    "amount": "238.50",
                    "currency": "CNY",
                    "due_date": "2026-09-01",
                    "received_at": "",
                    "status": "due",
                    "evidence_reference": "INVOICE-EVIDENCE-1",
                },
            ),
            (
                "renewal",
                {
                    "renewal_id": "REN-1",
                    "customer_id": "CUS-1",
                    "contract_id": "CON-1",
                    "renewal_date": "2027-07-31",
                    "proposed_value": "300.00",
                    "currency": "CNY",
                    "status": "pending_review",
                    "evidence_reference": "RENEWAL-EVIDENCE-1",
                },
            ),
        ]

        results = [self.upsert(entity_type, data) for entity_type, data in fixtures]
        audit_count = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        self.assertEqual(audit_count, 9)
        self.assertTrue(all(isinstance(row["audit_event_id"], int) for row in results))

    def test_requires_explicit_human_confirmation(self):
        with self.assertRaisesRegex(ValueError, "human confirmation required"):
            self.upsert("customer", self.customer(), confirmed=False)

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], 0)

    def test_duplicate_contact_email_rolls_back_without_audit(self):
        self.upsert("customer", self.customer())
        self.upsert("contact", self.contact())
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        with self.assertRaisesRegex(ValueError, "duplicate customer contact"):
            self.upsert("contact", self.contact("CONT-2", email=" BUYER@EXAMPLE.INVALID "))

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM contacts").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_duplicate_quotation_version_and_contract_reference_roll_back(self):
        self.upsert("customer", self.customer())
        self.upsert("quotation", self.quotation())

        with self.assertRaisesRegex(ValueError, "duplicate quotation version"):
            self.upsert("quotation", self.quotation("QUOTE-2"))

        self.upsert("contract", self.contract())
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        with self.assertRaisesRegex(ValueError, "duplicate contract reference"):
            self.upsert("contract", self.contract("CON-2", reference=" ctr-2026-001 "))

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM contract_records").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_contract_customer_must_match_quotation_customer(self):
        self.upsert("customer", self.customer())
        self.upsert("customer", self.customer("CUS-2"))
        self.upsert("quotation", self.quotation())
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        with self.assertRaisesRegex(ValueError, "contract customer must match quotation customer"):
            self.upsert("contract", self.contract(customer_id="CUS-2"))

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM contract_records").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_invalid_money_currency_and_digest_do_not_mutate_database(self):
        self.seed_contract()
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        payment = {
            "payment_id": "PAY-BAD",
            "customer_id": "CUS-1",
            "contract_id": "CON-1",
            "amount": "0",
            "currency": "CNY",
            "due_date": "2026-09-01",
            "received_at": "",
            "status": "due",
            "evidence_reference": "PAY-EVIDENCE",
        }

        with self.assertRaisesRegex(ValueError, "amount must be positive"):
            self.upsert("payment", payment)
        with self.assertRaisesRegex(ValueError, "currency must be a three-letter code"):
            self.upsert("payment", {**payment, "amount": "10", "currency": "RMB1"})
        with self.assertRaisesRegex(ValueError, "document_digest must be sha256"):
            self.upsert("contract", {**self.contract(), "document_digest": "latest"})

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM payment_records").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_rejects_sensitive_or_full_content_fields(self):
        with self.assertRaisesRegex(ValueError, "unsupported customer fields: bank_account"):
            self.upsert("customer", {**self.customer(), "bank_account": "do-not-store"})

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0], 0)

    def test_query_returns_only_requested_allowed_fields(self):
        self.upsert("customer", self.customer())

        result = MODULE.query_record(
            self.connection, "customer", "CUS-1", ["customer_id", "display_name", "status"]
        )

        self.assertEqual(
            result,
            {"customer_id": "CUS-1", "display_name": "Customer CUS-1", "status": "active"},
        )
        with self.assertRaisesRegex(ValueError, "unsupported query fields"):
            MODULE.query_record(self.connection, "customer", "CUS-1", ["display_name", "bank_account"])

    def test_update_audit_contains_before_and_after_values(self):
        self.upsert("customer", self.customer())
        self.upsert("customer", {**self.customer(), "status": "inactive"})

        row = self.connection.execute(
            "SELECT action, before_json, after_json FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()

        self.assertEqual(row["action"], "update")
        self.assertEqual(json.loads(row["before_json"])["status"], "active")
        self.assertEqual(json.loads(row["after_json"])["status"], "inactive")


if __name__ == "__main__":
    unittest.main()
