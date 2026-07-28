#!/usr/bin/env python3
"""Create an evidence-backed pre-award supplier scorecard without selecting a supplier."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
from typing import Any


DIMENSIONS = ("qualification", "price", "delivery", "quality", "risk")
TWO_PLACES = Decimal("0.01")


def _decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid number") from None
    if not number.is_finite():
        raise ValueError(f"{field} must be finite")
    return number


def _weights(raw: Any) -> dict[str, Decimal]:
    if not isinstance(raw, dict) or set(raw) != set(DIMENSIONS):
        raise ValueError(f"weights must contain {', '.join(DIMENSIONS)}")
    weights = {name: _decimal(raw[name], f"{name} weight") for name in DIMENSIONS}
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("weights must be non-negative")
    if sum(weights.values(), Decimal("0")) != Decimal("1"):
        raise ValueError("weights must sum to 1")
    return weights


def score_suppliers(data: dict[str, Any]) -> dict[str, Any]:
    """Calculate comparable scores; missing evidence keeps a supplier unranked."""
    for field in ("scoring_id", "request_id", "rfq_id", "weights", "suppliers"):
        if data.get(field) in (None, ""):
            raise ValueError(f"missing field: {field}")
    if not isinstance(data["suppliers"], list) or not data["suppliers"]:
        raise ValueError("suppliers must be a non-empty list")

    weights = _weights(data["weights"])
    rows: list[dict[str, Any]] = []
    supplier_ids: list[str] = []
    for supplier in data["suppliers"]:
        supplier_id = str(supplier.get("supplier_id", "")).strip()
        if not supplier_id:
            raise ValueError("supplier_id must not be blank")
        supplier_ids.append(supplier_id)
        findings: list[str] = []
        normalized: dict[str, dict[str, str]] = {}
        weighted = Decimal("0")
        for dimension in DIMENSIONS:
            value = supplier.get(dimension)
            if not isinstance(value, dict):
                findings.append(f"missing {dimension} score")
                continue
            score = _decimal(value.get("score"), f"{dimension} score")
            if score < 0 or score > 5:
                raise ValueError(f"{dimension} score must be between 0 and 5")
            evidence = str(value.get("evidence_reference", "")).strip()
            if not evidence:
                findings.append(f"missing {dimension} evidence")
            normalized[dimension] = {
                "score": format(score, "f"),
                "evidence_reference": evidence,
            }
            weighted += score * weights[dimension]

        eligible = not findings and set(normalized) == set(DIMENSIONS)
        rows.append(
            {
                "supplier_id": supplier_id,
                "dimensions": normalized,
                "weighted_score": format(
                    weighted.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"
                )
                if eligible
                else None,
                "eligible": eligible,
                "blocking_findings": findings,
                "rank": None,
                "_weighted": weighted,
            }
        )

    if len(set(supplier_ids)) != len(supplier_ids):
        raise ValueError("duplicate supplier_id")
    eligible_rows = [row for row in rows if row["eligible"]]
    for rank, row in enumerate(
        sorted(eligible_rows, key=lambda item: (-item["_weighted"], item["supplier_id"])),
        start=1,
    ):
        row["rank"] = rank
    for row in rows:
        row.pop("_weighted")

    return {
        "scoring_id": str(data["scoring_id"]),
        "request_id": str(data["request_id"]),
        "rfq_id": str(data["rfq_id"]),
        "weights": {name: format(weights[name], "f") for name in DIMENSIONS},
        "suppliers": rows,
        "decision_status": "human_review_required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Supplier scoring JSON")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(score_suppliers(data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
