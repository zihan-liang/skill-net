#!/usr/bin/env python3
"""Calculate an evidence-backed supplier performance score for human review."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
from typing import Any


DEFAULT_WEIGHTS = {
    "delivery": Decimal("0.25"),
    "quality": Decimal("0.30"),
    "service": Decimal("0.20"),
    "commercial_performance": Decimal("0.15"),
    "compliance": Decimal("0.10"),
}
TWO_PLACES = Decimal("0.01")


def _decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid number") from None
    if not number.is_finite():
        raise ValueError(f"{field} must be finite")
    return number


def _weights(data: dict[str, Any]) -> dict[str, Decimal]:
    raw = data.get("weights")
    if raw is None:
        return dict(DEFAULT_WEIGHTS)
    if set(raw) != set(DEFAULT_WEIGHTS):
        raise ValueError("weights must contain all five supported dimensions")
    weights = {name: _decimal(value, f"{name} weight") for name, value in raw.items()}
    if any(value < 0 for value in weights.values()):
        raise ValueError("weights must be non-negative")
    if sum(weights.values(), Decimal("0")) != Decimal("1"):
        raise ValueError("weights must sum to 1")
    return weights


def _band(score: Decimal | None) -> str:
    if score is None:
        return "insufficient_evidence"
    if score >= Decimal("4.5"):
        return "excellent"
    if score >= Decimal("3.5"):
        return "strong"
    if score >= Decimal("2.5"):
        return "acceptable"
    if score >= Decimal("1.5"):
        return "needs_improvement"
    return "critical"


def evaluate_supplier(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate only dimensions that include a valid score and evidence reference."""
    missing_header = [
        field
        for field in ("evaluation_id", "supplier_id", "period", "dimensions")
        if data.get(field) in (None, "")
    ]
    if missing_header:
        raise ValueError(f"missing evaluation fields: {', '.join(missing_header)}")
    dimensions = data["dimensions"]
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions must be an object")
    unknown = sorted(set(dimensions) - set(DEFAULT_WEIGHTS))
    if unknown:
        raise ValueError(f"unsupported dimensions: {', '.join(unknown)}")
    weights = _weights(data)

    result_dimensions: dict[str, dict[str, Any]] = {}
    missing_evidence: list[str] = []
    included_weight = Decimal("0")
    weighted_total = Decimal("0")
    evidence_references: list[str] = []

    for name in DEFAULT_WEIGHTS:
        item = dimensions.get(name)
        if not isinstance(item, dict) or item.get("score") in (None, ""):
            missing_evidence.append(name)
            result_dimensions[name] = {
                "score": None,
                "weight": format(weights[name], "f"),
                "evidence_reference": None,
                "included": False,
            }
            continue
        score = _decimal(item["score"], f"{name} score")
        if score < 0 or score > 5:
            raise ValueError(f"{name} score must be between 0 and 5")
        reference = str(item.get("evidence_reference", "")).strip()
        included = bool(reference)
        if included:
            included_weight += weights[name]
            weighted_total += score * weights[name]
            evidence_references.append(reference)
        else:
            missing_evidence.append(name)
        result_dimensions[name] = {
            "score": format(score.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"),
            "weight": format(weights[name], "f"),
            "evidence_reference": reference or None,
            "included": included,
        }

    normalized = weighted_total / included_weight if included_weight else None
    score_text = (
        format(normalized.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f")
        if normalized is not None
        else None
    )
    coverage = included_weight * Decimal("100")
    return {
        "evaluation_id": str(data["evaluation_id"]),
        "supplier_id": str(data["supplier_id"]),
        "period": str(data["period"]),
        "weights": {name: format(value, "f") for name, value in weights.items()},
        "dimensions": result_dimensions,
        "weighted_score": score_text,
        "evidence_coverage_percent": format(
            coverage.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"
        ),
        "performance_band": _band(normalized),
        "missing_evidence": sorted(set(missing_evidence)),
        "evidence_references": evidence_references,
        "decision_status": "human_review_required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path, help="Evaluation JSON")
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_supplier(data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
