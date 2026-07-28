#!/usr/bin/env python3
"""Evaluate a business opportunity without making the human decision."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any


DIMENSIONS = (
    "strategic_fit",
    "need_clarity",
    "authority_access",
    "budget_readiness",
    "timeline_readiness",
    "delivery_fit",
)
DEFAULT_WEIGHTS = {
    "strategic_fit": Decimal("0.20"),
    "need_clarity": Decimal("0.20"),
    "authority_access": Decimal("0.15"),
    "budget_readiness": Decimal("0.15"),
    "timeline_readiness": Decimal("0.10"),
    "delivery_fit": Decimal("0.20"),
}


def _required_text(data: dict[str, Any], *fields: str) -> None:
    missing = [field for field in fields if not str(data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")


def _decimal(value: Any, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be numeric") from None
    if not number.is_finite():
        raise ValueError(f"{label} must be finite")
    return number


def _weights(data: dict[str, Any]) -> dict[str, Decimal]:
    supplied = data.get("weights")
    if supplied is None:
        return dict(DEFAULT_WEIGHTS)
    if not isinstance(supplied, dict) or set(supplied) != set(DIMENSIONS):
        raise ValueError("weights must match required set")
    result = {name: _decimal(supplied[name], f"weight {name}") for name in DIMENSIONS}
    if any(value < 0 for value in result.values()):
        raise ValueError("weights must be non-negative")
    if sum(result.values(), Decimal("0")) != Decimal("1"):
        raise ValueError("weights must sum to 1")
    return result


def evaluate_opportunity(data: dict[str, Any]) -> dict[str, Any]:
    """Return an evidence-aware score and preserve the human decision boundary."""
    if not isinstance(data, dict):
        raise ValueError("opportunity data must be an object")
    _required_text(data, "customer_id", "opportunity_id")

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        raise ValueError("dimensions must match required set")
    weights = _weights(data)

    blocking_findings: list[str] = []
    normalized_dimensions: dict[str, dict[str, str]] = {}
    weighted_score = Decimal("0")
    evidence_count = 0

    for name in DIMENSIONS:
        entry = dimensions[name]
        if not isinstance(entry, dict):
            raise ValueError(f"dimension {name} must be an object")
        score = _decimal(entry.get("score"), f"dimension {name} score")
        if score < 0 or score > 5:
            raise ValueError(f"dimension {name} score must be between 0 and 5")
        evidence = str(entry.get("evidence_reference", "")).strip()
        if evidence:
            evidence_count += 1
        else:
            blocking_findings.append(f"missing evidence for dimension: {name}")
        weighted_score += score * weights[name]
        normalized_dimensions[name] = {
            "score": f"{score:.2f}",
            "weight": f"{weights[name]:.2f}",
            "evidence_reference": evidence,
        }

    risks = data.get("risks", [])
    if not isinstance(risks, list):
        raise ValueError("risks must be a list")
    normalized_risks: list[dict[str, str]] = []
    risk_ids: set[str] = set()
    for risk in risks:
        if not isinstance(risk, dict):
            raise ValueError("risk must be an object")
        _required_text(risk, "risk_id", "severity", "status")
        risk_id = str(risk["risk_id"]).strip()
        if risk_id in risk_ids:
            raise ValueError(f"duplicate risk_id: {risk_id}")
        risk_ids.add(risk_id)
        severity = str(risk["severity"]).strip().lower()
        status = str(risk["status"]).strip().lower()
        if severity not in {"low", "medium", "high", "critical"}:
            raise ValueError(f"unsupported risk severity: {severity}")
        if status not in {"open", "mitigating", "accepted", "closed"}:
            raise ValueError(f"unsupported risk status: {status}")
        evidence = str(risk.get("evidence_reference", "")).strip()
        if severity == "critical" and status in {"open", "mitigating"}:
            blocking_findings.append(f"open critical risk: {risk_id}")
        if not evidence:
            blocking_findings.append(f"missing evidence for risk: {risk_id}")
        normalized_risks.append(
            {"risk_id": risk_id, "severity": severity, "status": status, "evidence_reference": evidence}
        )

    passed = not blocking_findings
    coverage = Decimal(evidence_count) / Decimal(len(DIMENSIONS)) * Decimal("100")
    return {
        "customer_id": str(data["customer_id"]).strip(),
        "opportunity_id": str(data["opportunity_id"]).strip(),
        "dimensions": normalized_dimensions,
        "weighted_score_out_of_5": f"{weighted_score:.2f}",
        "evidence_coverage_percent": f"{coverage:.2f}",
        "risks": normalized_risks,
        "blocking_findings": blocking_findings,
        "automated_readiness_passed": passed,
        "decision_status": "human_review_required" if passed else "blocked",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate an evidence-backed business opportunity without making the decision."
    )
    parser.add_argument("--data", required=True, type=Path, help="Opportunity assessment JSON")
    args = parser.parse_args()
    payload = json.loads(args.data.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_opportunity(payload), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
