#!/usr/bin/env python3
"""Validate release controls without deploying, changing, or rolling back a system."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ENVIRONMENTS = {"local", "development", "test", "staging", "production"}
DIGEST = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


def _list_control(
    manifest: dict[str, Any], field: str, finding: str
) -> tuple[list[str], bool]:
    value = manifest.get(field)
    if value is None:
        return [], False
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    normalized = [str(item).strip() for item in value]
    valid = bool(normalized) and all(normalized)
    return normalized if valid else [], valid


def validate_release_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic readiness findings while performing no external action."""
    core_fields = ("release_id", "system_id", "version_id", "environment", "artifact_digest")
    missing = [field for field in core_fields if manifest.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing release manifest fields: {', '.join(missing)}")
    environment = str(manifest["environment"]).strip().lower()
    if environment not in ENVIRONMENTS:
        raise ValueError("unsupported environment")
    digest = str(manifest["artifact_digest"]).strip()
    if not DIGEST.fullmatch(digest):
        raise ValueError("artifact_digest must be sha256:<64 hexadecimal characters>")
    digest = digest.lower()

    findings: list[str] = []
    scalar_controls = {
        "change_reference": "missing approved change reference",
        "test_acceptance_reference": "missing test acceptance reference",
        "release_owner": "missing release owner",
        "rollback_owner": "missing rollback owner",
        "maintenance_window": "missing maintenance window",
        "backup_reference": "missing backup or recovery reference",
    }
    normalized_scalars: dict[str, str | None] = {}
    for field, finding in scalar_controls.items():
        value = str(manifest.get(field, "")).strip()
        normalized_scalars[field] = value or None
        if not value:
            findings.append(finding)

    list_controls = {
        "deployment_steps": "missing deployment steps",
        "rollback_steps": "missing rollback steps",
        "health_checks": "missing health checks",
        "monitoring_checks": "missing monitoring checks",
        "communication_plan": "missing communication plan",
    }
    normalized_lists: dict[str, list[str]] = {}
    list_results: dict[str, bool] = {}
    for field, finding in list_controls.items():
        normalized, valid = _list_control(manifest, field, finding)
        normalized_lists[field] = normalized
        list_results[field] = valid
        if not valid:
            findings.append(finding)

    production_approval = str(
        manifest.get("production_approval_reference", "")
    ).strip()
    if environment == "production" and not production_approval:
        findings.append("missing production approval reference")

    readiness_checks = {
        "immutable_artifact": True,
        "approved_change": bool(normalized_scalars["change_reference"]),
        "test_accepted": bool(normalized_scalars["test_acceptance_reference"]),
        "owners_assigned": bool(
            normalized_scalars["release_owner"] and normalized_scalars["rollback_owner"]
        ),
        "maintenance_window_defined": bool(normalized_scalars["maintenance_window"]),
        "deployment_plan_defined": list_results["deployment_steps"],
        "rollback_plan_defined": list_results["rollback_steps"],
        "backup_or_recovery_defined": bool(normalized_scalars["backup_reference"]),
        "health_checks_defined": list_results["health_checks"],
        "monitoring_defined": list_results["monitoring_checks"],
        "communications_defined": list_results["communication_plan"],
        "production_approval_present": environment != "production" or bool(production_approval),
    }
    ready = not findings
    return {
        "release_id": str(manifest["release_id"]),
        "system_id": str(manifest["system_id"]),
        "version_id": str(manifest["version_id"]),
        "environment": environment,
        "artifact_digest": digest,
        **normalized_scalars,
        **normalized_lists,
        "production_approval_reference": production_approval or None,
        "readiness_checks": readiness_checks,
        "blocking_findings": findings,
        "automated_readiness_passed": ready,
        "release_status": "ready_for_human_release" if ready else "blocked",
        "external_action": "not_performed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Release manifest JSON")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(json.dumps(validate_release_manifest(manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
