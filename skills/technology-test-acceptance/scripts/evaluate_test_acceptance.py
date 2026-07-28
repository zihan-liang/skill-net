#!/usr/bin/env python3
"""Evaluate test evidence and automated gates without making human acceptance."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
from typing import Any


TWO_PLACES = Decimal("0.01")
ENVIRONMENTS = {"local", "development", "test", "staging", "production"}
SEVERITIES = {"critical", "high", "medium", "low"}
DEFECT_STATUSES = {"open", "in_progress", "resolved", "accepted"}


def _decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid number") from None
    if not number.is_finite():
        raise ValueError(f"{field} must be finite")
    return number


def _percent(value: Any, field: str) -> Decimal:
    number = _decimal(value, field)
    if number < 0 or number > 100:
        raise ValueError(f"{field} must be between 0 and 100")
    return number


def _count(value: Any, field: str) -> int:
    number = _decimal(value, field)
    if number < 0 or number != number.to_integral_value():
        raise ValueError(f"{field} must be a non-negative integer")
    return int(number)


def evaluate_test_acceptance(data: dict[str, Any]) -> dict[str, Any]:
    """Recompute test totals and return blocking findings plus a human-review state."""
    header_fields = (
        "test_run_id",
        "system_id",
        "version_id",
        "environment",
        "required_suites",
        "minimum_pass_rate_percent",
        "minimum_coverage_percent",
        "coverage_percent",
        "suites",
        "defects",
    )
    missing = [field for field in header_fields if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing test acceptance fields: {', '.join(missing)}")
    environment = str(data["environment"]).strip().lower()
    if environment not in ENVIRONMENTS:
        raise ValueError("unsupported environment")
    required_suites = data["required_suites"]
    suites = data["suites"]
    defects = data["defects"]
    if not isinstance(required_suites, list) or not required_suites:
        raise ValueError("required_suites must be a non-empty list")
    if not isinstance(suites, list) or not suites:
        raise ValueError("suites must be a non-empty list")
    if not isinstance(defects, list):
        raise ValueError("defects must be a list")

    required = [str(value).strip() for value in required_suites]
    if any(not value for value in required) or len(set(required)) != len(required):
        raise ValueError("required_suites must contain unique non-blank IDs")
    minimum_pass = _percent(data["minimum_pass_rate_percent"], "minimum_pass_rate_percent")
    minimum_coverage = _percent(
        data["minimum_coverage_percent"], "minimum_coverage_percent"
    )
    coverage = _percent(data["coverage_percent"], "coverage_percent")

    normalized_suites: list[dict[str, Any]] = []
    suite_ids: set[str] = set()
    totals = {"executed": 0, "passed": 0, "failed": 0, "skipped": 0}
    findings: list[str] = []
    evidence_references: list[str] = []
    for suite in suites:
        fields = ("suite_id", "executed", "passed", "failed", "skipped")
        missing_suite = [field for field in fields if suite.get(field) in (None, "")]
        if missing_suite:
            raise ValueError(f"missing suite fields: {', '.join(missing_suite)}")
        suite_id = str(suite["suite_id"]).strip()
        if suite_id in suite_ids:
            raise ValueError(f"duplicate suite_id: {suite_id}")
        suite_ids.add(suite_id)
        counts = {name: _count(suite[name], name) for name in totals}
        if counts["executed"] != counts["passed"] + counts["failed"] + counts["skipped"]:
            raise ValueError(f"suite {suite_id} counts do not reconcile")
        for name in totals:
            totals[name] += counts[name]
        reference = str(suite.get("evidence_reference", "")).strip()
        if not reference:
            findings.append(f"missing evidence for suite: {suite_id}")
        else:
            evidence_references.append(reference)
        normalized_suites.append(
            {"suite_id": suite_id, **counts, "evidence_reference": reference or None}
        )

    for suite_id in sorted(set(required) - suite_ids):
        findings.append(f"missing required suite: {suite_id}")
    if totals["executed"] == 0:
        pass_rate = Decimal("0")
        findings.append("no tests executed")
    else:
        pass_rate = Decimal(totals["passed"]) * Decimal("100") / Decimal(totals["executed"])
    pass_rate_text = format(pass_rate.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f")
    minimum_pass_text = format(minimum_pass.quantize(TWO_PLACES), "f")
    coverage_text = format(coverage.quantize(TWO_PLACES), "f")
    minimum_coverage_text = format(minimum_coverage.quantize(TWO_PLACES), "f")
    if totals["failed"]:
        findings.append(f"failed tests present: {totals['failed']}")
    if pass_rate < minimum_pass:
        findings.append(f"pass rate below threshold: {pass_rate_text} < {minimum_pass_text}")
    if coverage < minimum_coverage:
        findings.append(f"coverage below threshold: {coverage_text} < {minimum_coverage_text}")

    normalized_defects: list[dict[str, Any]] = []
    defect_ids: set[str] = set()
    for defect in defects:
        fields = ("defect_id", "severity", "status", "evidence_reference")
        missing_defect = [field for field in fields if defect.get(field) in (None, "")]
        if missing_defect:
            raise ValueError(f"missing defect fields: {', '.join(missing_defect)}")
        defect_id = str(defect["defect_id"]).strip()
        if defect_id in defect_ids:
            raise ValueError(f"duplicate defect_id: {defect_id}")
        defect_ids.add(defect_id)
        severity = str(defect["severity"]).strip().lower()
        status = str(defect["status"]).strip().lower()
        if severity not in SEVERITIES:
            raise ValueError(f"unsupported defect severity: {severity}")
        if status not in DEFECT_STATUSES:
            raise ValueError(f"unsupported defect status: {status}")
        reference = str(defect["evidence_reference"]).strip()
        evidence_references.append(reference)
        if severity in {"critical", "high"} and status in {"open", "in_progress"}:
            findings.append(f"open {severity} defect: {defect_id}")
        normalized_defects.append(
            {
                "defect_id": defect_id,
                "severity": severity,
                "status": status,
                "evidence_reference": reference,
            }
        )

    gate_passed = not findings
    return {
        "test_run_id": str(data["test_run_id"]),
        "system_id": str(data["system_id"]),
        "version_id": str(data["version_id"]),
        "environment": environment,
        "required_suites": required,
        "suites": normalized_suites,
        "totals": totals,
        "pass_rate_percent": pass_rate_text,
        "minimum_pass_rate_percent": minimum_pass_text,
        "coverage_percent": coverage_text,
        "minimum_coverage_percent": minimum_coverage_text,
        "defects": normalized_defects,
        "blocking_findings": findings,
        "evidence_references": list(dict.fromkeys(evidence_references)),
        "automated_gate_passed": gate_passed,
        "acceptance_status": "human_review_required" if gate_passed else "blocked",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path, help="Test-acceptance JSON")
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_test_acceptance(data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
