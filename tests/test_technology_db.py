#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "technology-database"
    / "scripts"
    / "technology_db.py"
)
SPEC = spec_from_file_location("technology_db", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class TechnologyDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        self.connection = MODULE.connect_database(self.temp.name)
        MODULE.initialize_database(self.connection)
        self.audit = {
            "actor": "technology-demo",
            "business_purpose": "SkillNet technology workflow test",
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

    def system(self, system_id="SYS-1"):
        return {
            "system_id": system_id,
            "name": f"System {system_id}",
            "owner": "Technology Team",
            "criticality": "high",
            "environment_scope": "development,test,staging,production",
            "status": "active",
        }

    def version(self, version_id="VER-1", system_id="SYS-1", label="1.0.0"):
        return {
            "version_id": version_id,
            "system_id": system_id,
            "version_label": label,
            "artifact_digest": "sha256:" + "a" * 64,
            "environment": "staging",
            "status": "released",
            "released_at": "2026-07-28T10:00:00+08:00",
            "evidence_reference": "REL-1",
        }

    def seed_system_and_version(self):
        self.upsert("system", self.system())
        self.upsert("system_version", self.version())

    def test_initializes_all_technology_tables(self):
        rows = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        names = {row[0] for row in rows}

        self.assertTrue(
            {
                "architectures",
                "systems",
                "projects",
                "code_repositories",
                "api_documents",
                "test_records",
                "incidents",
                "maintenance_records",
                "system_versions",
                "audit_log",
            }
            <= names
        )

    def test_records_every_supported_entity_with_audit_events(self):
        fixtures = [
            ("system", self.system()),
            (
                "architecture",
                {
                    "architecture_id": "ARCH-1",
                    "system_id": "SYS-1",
                    "version": "1",
                    "title": "Onboarding architecture",
                    "status": "approved",
                    "document_reference": "DOC-ARCH-1",
                },
            ),
            (
                "project",
                {
                    "project_id": "PROJ-1",
                    "system_id": "SYS-1",
                    "name": "Onboarding service",
                    "owner": "Technology Team",
                    "status": "active",
                },
            ),
            (
                "code_repository",
                {
                    "repository_id": "REPO-1",
                    "project_id": "PROJ-1",
                    "provider": "GitHub",
                    "repository_reference": "github:example/onboarding",
                    "default_branch": "main",
                    "commit_hash": "a1b2c3d4",
                    "status": "active",
                },
            ),
            ("system_version", self.version()),
            (
                "api_document",
                {
                    "api_document_id": "API-1",
                    "system_id": "SYS-1",
                    "version": "1.0",
                    "interface_name": "Onboarding API",
                    "document_reference": "DOC-API-1",
                    "status": "published",
                },
            ),
            (
                "test_record",
                {
                    "test_record_id": "TEST-1",
                    "system_id": "SYS-1",
                    "version_id": "VER-1",
                    "environment": "staging",
                    "result": "passed",
                    "evidence_reference": "TEST-RUN-1",
                    "executed_at": "2026-07-28T09:00:00+08:00",
                },
            ),
            (
                "incident",
                {
                    "incident_id": "INC-1",
                    "system_id": "SYS-1",
                    "version_id": "VER-1",
                    "environment": "staging",
                    "severity": "medium",
                    "status": "resolved",
                    "opened_at": "2026-07-28T11:00:00+08:00",
                    "evidence_reference": "INCIDENT-1",
                },
            ),
            (
                "maintenance_record",
                {
                    "maintenance_id": "MAINT-1",
                    "system_id": "SYS-1",
                    "version_id": "VER-1",
                    "environment": "staging",
                    "maintenance_type": "patch",
                    "status": "completed",
                    "performed_at": "2026-07-28T12:00:00+08:00",
                    "evidence_reference": "MAINTENANCE-1",
                },
            ),
        ]

        results = [self.upsert(entity_type, data) for entity_type, data in fixtures]
        count = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        self.assertEqual(count, 9)
        self.assertTrue(all(isinstance(row["audit_event_id"], int) for row in results))

    def test_requires_explicit_human_confirmation(self):
        with self.assertRaisesRegex(ValueError, "human confirmation required"):
            self.upsert("system", self.system(), confirmed=False)

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM systems").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], 0)

    def test_duplicate_repository_reference_rolls_back_without_audit(self):
        self.upsert("system", self.system())
        self.upsert(
            "project",
            {
                "project_id": "PROJ-1",
                "system_id": "SYS-1",
                "name": "Onboarding",
                "owner": "Technology Team",
                "status": "active",
            },
        )
        first = {
            "repository_id": "REPO-1",
            "project_id": "PROJ-1",
            "provider": "GitHub",
            "repository_reference": "github:example/onboarding",
            "default_branch": "main",
            "commit_hash": "a1b2c3d4",
            "status": "active",
        }
        self.upsert("code_repository", first)
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        with self.assertRaisesRegex(ValueError, "duplicate repository reference"):
            self.upsert(
                "code_repository",
                {**first, "repository_id": "REPO-2", "repository_reference": " GITHUB:EXAMPLE/ONBOARDING "},
            )

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM code_repositories").fetchone()[0], 1)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_duplicate_system_version_rolls_back_without_audit(self):
        self.upsert("system", self.system())
        self.upsert("system_version", self.version())

        with self.assertRaisesRegex(ValueError, "duplicate system version"):
            self.upsert("system_version", self.version("VER-2"))

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM system_versions").fetchone()[0], 1)

    def test_invalid_environment_and_digest_do_not_mutate_database(self):
        self.upsert("system", self.system())
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        with self.assertRaisesRegex(ValueError, "unsupported environment"):
            self.upsert("system_version", {**self.version(), "environment": "unknown"})
        with self.assertRaisesRegex(ValueError, "artifact_digest must be sha256"):
            self.upsert("system_version", {**self.version(), "artifact_digest": "latest"})

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM system_versions").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_record_system_must_match_version_system(self):
        self.upsert("system", self.system())
        self.upsert("system", self.system("SYS-2"))
        self.upsert("system_version", self.version())
        audit_before = self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        with self.assertRaisesRegex(ValueError, "record system must match system version"):
            self.upsert(
                "test_record",
                {
                    "test_record_id": "TEST-BAD",
                    "system_id": "SYS-2",
                    "version_id": "VER-1",
                    "environment": "staging",
                    "result": "passed",
                    "evidence_reference": "BAD",
                    "executed_at": "2026-07-28T09:00:00+08:00",
                },
            )

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM test_records").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0], audit_before)

    def test_rejects_source_body_and_secret_fields(self):
        with self.assertRaisesRegex(ValueError, "unsupported system fields: secret"):
            self.upsert("system", {**self.system(), "secret": "do-not-store"})

        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM systems").fetchone()[0], 0)

    def test_query_returns_only_requested_allowed_fields(self):
        self.upsert("system", self.system())

        result = MODULE.query_record(
            self.connection, "system", "SYS-1", ["system_id", "name", "status"]
        )

        self.assertEqual(
            result,
            {"system_id": "SYS-1", "name": "System SYS-1", "status": "active"},
        )
        with self.assertRaisesRegex(ValueError, "unsupported query fields"):
            MODULE.query_record(self.connection, "system", "SYS-1", ["name", "secret"])

    def test_update_audit_contains_before_and_after_values(self):
        self.upsert("system", self.system())
        self.upsert("system", {**self.system(), "status": "maintenance"})

        row = self.connection.execute(
            "SELECT action, before_json, after_json FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()

        self.assertEqual(row["action"], "update")
        self.assertEqual(json.loads(row["before_json"])["status"], "active")
        self.assertEqual(json.loads(row["after_json"])["status"], "maintenance")


if __name__ == "__main__":
    unittest.main()
