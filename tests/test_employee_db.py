#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sqlite3
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "hr-employee-database"
    / "scripts"
    / "employee_db.py"
)
SPEC = spec_from_file_location("employee_db", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class EmployeeDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        self.connection = MODULE.connect_database(self.temp.name)
        MODULE.initialize_database(self.connection)

    def tearDown(self):
        self.connection.close()
        self.temp.close()

    def test_initializes_required_tables(self):
        rows = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        names = {row[0] for row in rows}

        self.assertTrue(
            {"employees", "employee_skills", "kpi_records", "training_records", "audit_log"}
            <= names
        )

    def test_upserts_employee_and_records_audit_event(self):
        employee = {
            "employee_id": "E-001",
            "legal_name": "Lin Chen",
            "department": "Product",
            "job_title": "AI Product Manager",
            "employment_status": "active",
        }

        result = MODULE.upsert_employee(self.connection, employee, actor="hr@example.com")
        audit = self.connection.execute(
            "SELECT actor, action, entity_id FROM audit_log"
        ).fetchone()

        self.assertEqual(result["employee_id"], "E-001")
        self.assertIsInstance(result["audit_event_id"], int)
        self.assertEqual(tuple(audit), ("hr@example.com", "upsert", "E-001"))

    def test_updates_employee_skill_and_returns_summary(self):
        MODULE.upsert_employee(
            self.connection,
            {
                "employee_id": "E-002",
                "legal_name": "Wei Li",
                "department": "Engineering",
                "job_title": "ML Engineer",
                "employment_status": "active",
            },
            actor="hr@example.com",
        )
        MODULE.upsert_skill(
            self.connection,
            "E-002",
            {"skill_name": "Python", "proficiency": 4, "evidence": "Production service"},
            actor="manager@example.com",
        )

        summary = MODULE.get_employee_summary(self.connection, "E-002")

        self.assertEqual(summary["skills"][0]["skill_name"], "Python")
        self.assertEqual(summary["skills"][0]["proficiency"], 4)

    def test_records_kpi_and_training_with_audit_events(self):
        MODULE.upsert_employee(
            self.connection,
            {
                "employee_id": "E-003",
                "legal_name": "Ming Zhao",
                "department": "Growth",
                "job_title": "Growth Manager",
                "employment_status": "active",
            },
            actor="hr@example.com",
        )

        kpi = MODULE.add_kpi_record(
            self.connection,
            "E-003",
            {
                "period": "2026-Q3",
                "metric": "Activated members",
                "target": "1000",
                "actual": "920",
                "status": "in_progress",
            },
            actor="manager@example.com",
        )
        training = MODULE.add_training_record(
            self.connection,
            "E-003",
            {
                "course": "Personal Information Protection",
                "status": "completed",
                "completed_date": "2026-07-20",
                "credential": "TR-2026-031",
            },
            actor="hr@example.com",
        )
        summary = MODULE.get_employee_summary(self.connection, "E-003")

        self.assertIsInstance(kpi["audit_event_id"], int)
        self.assertIsInstance(training["audit_event_id"], int)
        self.assertEqual(summary["kpis"][0]["period"], "2026-Q3")
        self.assertEqual(summary["training"][0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
