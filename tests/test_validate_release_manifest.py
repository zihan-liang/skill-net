#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "technology-system-release"
    / "scripts"
    / "validate_release_manifest.py"
)
SPEC = spec_from_file_location("validate_release_manifest", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ReleaseManifestValidationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "release_id": "REL-1",
            "system_id": "SYS-1",
            "version_id": "VER-1",
            "environment": "staging",
            "artifact_digest": "sha256:" + "a" * 64,
            "change_reference": "CHANGE-1",
            "test_acceptance_reference": "TEST-ACCEPT-1",
            "release_owner": "Release Owner",
            "rollback_owner": "Rollback Owner",
            "maintenance_window": "2026-07-29T02:00:00+08:00/2026-07-29T03:00:00+08:00",
            "deployment_steps": ["Deploy immutable artifact", "Apply configuration"],
            "rollback_steps": ["Restore prior artifact", "Validate recovery"],
            "backup_reference": "BACKUP-1",
            "health_checks": ["API health returns success", "Error rate below threshold"],
            "monitoring_checks": ["Dashboard active", "Alerts routed to on-call"],
            "communication_plan": ["Notify release channel before and after change"],
            "production_approval_reference": "",
        }

    def test_complete_staging_manifest_is_ready_for_human_release(self):
        result = MODULE.validate_release_manifest(self.manifest)

        self.assertTrue(result["automated_readiness_passed"])
        self.assertEqual(result["release_status"], "ready_for_human_release")
        self.assertEqual(result["external_action"], "not_performed")

    def test_production_requires_approval_evidence(self):
        manifest = {**self.manifest, "environment": "production"}

        result = MODULE.validate_release_manifest(manifest)

        self.assertFalse(result["automated_readiness_passed"])
        self.assertIn("missing production approval reference", result["blocking_findings"])
        self.assertEqual(result["release_status"], "blocked")

    def test_approved_production_manifest_is_ready_for_human_release(self):
        manifest = {
            **self.manifest,
            "environment": "production",
            "production_approval_reference": "APP-PROD-1",
        }

        result = MODULE.validate_release_manifest(manifest)

        self.assertTrue(result["automated_readiness_passed"])
        self.assertEqual(result["release_status"], "ready_for_human_release")

    def test_rejects_malformed_artifact_digest(self):
        manifest = {**self.manifest, "artifact_digest": "latest"}

        with self.assertRaisesRegex(ValueError, "artifact_digest must be sha256"):
            MODULE.validate_release_manifest(manifest)

    def test_missing_rollback_steps_blocks_release(self):
        manifest = {**self.manifest, "rollback_steps": []}

        result = MODULE.validate_release_manifest(manifest)

        self.assertIn("missing rollback steps", result["blocking_findings"])
        self.assertEqual(result["release_status"], "blocked")

    def test_missing_health_and_monitoring_checks_are_reported(self):
        manifest = {**self.manifest, "health_checks": [], "monitoring_checks": []}

        result = MODULE.validate_release_manifest(manifest)

        self.assertIn("missing health checks", result["blocking_findings"])
        self.assertIn("missing monitoring checks", result["blocking_findings"])


if __name__ == "__main__":
    unittest.main()
