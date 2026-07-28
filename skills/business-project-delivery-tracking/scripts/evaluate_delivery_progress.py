#!/usr/bin/env python3
"""Evaluate weighted project delivery progress from milestone evidence."""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {"planned", "in_progress", "blocked", "completed", "accepted"}


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


def _date(value: Any, label: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValueError(f"{label} must be ISO date YYYY-MM-DD") from None


def evaluate_delivery_progress(data: dict[str, Any]) -> dict[str, Any]:
    """Calculate milestone completion and surface delivery findings."""
    if not isinstance(data, dict):
        raise ValueError("delivery data must be an object")
    _required_text(data, "contract_id", "project_id", "as_of_date")
    as_of_date = _date(data["as_of_date"], "as_of_date")
    milestones = data.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        raise ValueError("milestones must be a non-empty list")

    ids: set[str] = set()
    total_weight = Decimal("0")
    weighted_completion = Decimal("0")
    normalized: list[dict[str, str]] = []
    findings: list[str] = []

    for milestone in milestones:
        if not isinstance(milestone, dict):
            raise ValueError("milestone must be an object")
        _required_text(milestone, "milestone_id", "title", "owner", "due_date", "status")
        milestone_id = str(milestone["milestone_id"]).strip()
        if milestone_id in ids:
            raise ValueError(f"duplicate milestone_id: {milestone_id}")
        ids.add(milestone_id)
        weight = _decimal(milestone.get("weight_percent"), f"milestone {milestone_id} weight_percent")
        progress = _decimal(milestone.get("progress_percent"), f"milestone {milestone_id} progress_percent")
        if weight < 0:
            raise ValueError(f"milestone {milestone_id} weight_percent must be non-negative")
        if progress < 0 or progress > 100:
            raise ValueError(f"milestone {milestone_id} progress_percent must be between 0 and 100")
        status = str(milestone["status"]).strip().lower()
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"unsupported milestone status: {status}")
        if status == "planned" and progress != 0:
            raise ValueError(f"planned milestone {milestone_id} progress must be 0")
        if status == "in_progress" and not (Decimal("0") < progress < Decimal("100")):
            raise ValueError(f"in_progress milestone {milestone_id} progress must be between 0 and 100")
        if status in {"completed", "accepted"} and progress != 100:
            raise ValueError(f"{status} milestone {milestone_id} progress must be 100")

        due_date = _date(milestone["due_date"], f"milestone {milestone_id} due_date")
        evidence = str(milestone.get("evidence_reference", "")).strip()
        if status in {"completed", "accepted"} and not evidence:
            findings.append(f"missing completion evidence: {milestone_id}")
        if status == "blocked":
            findings.append(f"blocked milestone: {milestone_id}")
        if due_date < as_of_date and status not in {"completed", "accepted"}:
            findings.append(f"overdue milestone: {milestone_id}")

        total_weight += weight
        weighted_completion += weight * progress / Decimal("100")
        normalized.append(
            {
                "milestone_id": milestone_id,
                "title": str(milestone["title"]).strip(),
                "owner": str(milestone["owner"]).strip(),
                "weight_percent": f"{weight:.2f}",
                "due_date": due_date.isoformat(),
                "status": status,
                "progress_percent": f"{progress:.2f}",
                "evidence_reference": evidence,
            }
        )

    if total_weight != Decimal("100"):
        raise ValueError("milestone weights must sum to 100")
    passed = not findings
    return {
        "contract_id": str(data["contract_id"]).strip(),
        "project_id": str(data["project_id"]).strip(),
        "as_of_date": as_of_date.isoformat(),
        "milestone_count": len(normalized),
        "milestones": normalized,
        "weighted_completion_percent": f"{weighted_completion:.2f}",
        "blocking_findings": findings,
        "automated_health_passed": passed,
        "delivery_status": "on_track_human_review" if passed else "needs_attention",
        "external_action": "not_performed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate project delivery milestones without changing scope or claiming acceptance."
    )
    parser.add_argument("--data", required=True, type=Path, help="Delivery milestone JSON")
    args = parser.parse_args()
    payload = json.loads(args.data.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_delivery_progress(payload), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
