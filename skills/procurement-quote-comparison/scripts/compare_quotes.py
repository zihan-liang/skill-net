#!/usr/bin/env python3
"""Validate and compare supplier quotations without making an award decision."""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
import re
from typing import Any


DEFAULT_WEIGHTS = {
    "price": Decimal("0.40"),
    "delivery": Decimal("0.25"),
    "quality": Decimal("0.20"),
    "service": Decimal("0.15"),
}
CURRENCY = re.compile(r"^[A-Z]{3}$")
TWO_PLACES = Decimal("0.01")


def _required(data: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing {label} fields: {', '.join(missing)}")


def _decimal(value: Any, field: str, *, positive: bool = False) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid number") from None
    if not number.is_finite():
        raise ValueError(f"{field} must be finite")
    if positive and number <= 0:
        raise ValueError(f"{field} must be positive")
    return number


def _score(value: Any, field: str) -> Decimal:
    number = _decimal(value, field)
    if number < 0 or number > 5:
        raise ValueError(f"{field} must be between 0 and 5")
    return number


def _currency(value: Any) -> str:
    code = str(value).strip().upper()
    if not CURRENCY.fullmatch(code):
        raise ValueError("currency must be a three-letter code")
    return code


def _iso_date(value: Any, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValueError(f"{field} must be an ISO date") from None


def _weights(requirement: dict[str, Any]) -> dict[str, Decimal]:
    raw = requirement.get("weights")
    if raw is None:
        return dict(DEFAULT_WEIGHTS)
    if set(raw) != set(DEFAULT_WEIGHTS):
        raise ValueError("weights must contain price, delivery, quality, and service")
    weights = {name: _decimal(value, f"{name} weight") for name, value in raw.items()}
    if any(value < 0 for value in weights.values()):
        raise ValueError("weights must be non-negative")
    if sum(weights.values(), Decimal("0")) != Decimal("1"):
        raise ValueError("weights must sum to 1")
    return weights


def _required_items(requirement: dict[str, Any]) -> dict[str, Decimal]:
    items = requirement.get("required_items")
    if not isinstance(items, list) or not items:
        raise ValueError("required_items must be a non-empty list")
    normalized: dict[str, Decimal] = {}
    for item in items:
        _required(item, ("item_id", "quantity"), "required item")
        item_id = str(item["item_id"]).strip()
        if item_id in normalized:
            raise ValueError(f"duplicate required item_id: {item_id}")
        normalized[item_id] = _decimal(item["quantity"], "quantity", positive=True)
    return normalized


def _quote_row(
    quote: dict[str, Any], required_items: dict[str, Decimal], currency: str, on_date: date
) -> dict[str, Any]:
    _required(
        quote,
        (
            "quote_id",
            "supplier_id",
            "currency",
            "valid_until",
            "items",
            "delivery_days",
            "quality_score",
            "service_score",
        ),
        "quote",
    )
    if not isinstance(quote["items"], list) or not quote["items"]:
        raise ValueError("quote items must be a non-empty list")

    quoted_quantities: dict[str, Decimal] = {}
    total = Decimal("0")
    for item in quote["items"]:
        _required(item, ("item_id", "quantity", "unit_price"), "quote item")
        item_id = str(item["item_id"]).strip()
        if item_id in quoted_quantities:
            raise ValueError(f"duplicate quote item_id: {item_id}")
        quantity = _decimal(item["quantity"], "quantity", positive=True)
        unit_price = _decimal(item["unit_price"], "unit_price", positive=True)
        quoted_quantities[item_id] = quantity
        total += quantity * unit_price

    quote_currency = _currency(quote["currency"])
    valid_until = _iso_date(quote["valid_until"], "valid_until")
    delivery_days = _decimal(quote["delivery_days"], "delivery_days", positive=True)
    quality = _score(quote["quality_score"], "quality_score")
    service = _score(quote["service_score"], "service_score")

    findings: list[str] = []
    if quote_currency != currency:
        findings.append(f"currency mismatch: {quote_currency} != {currency}")
    if valid_until < on_date:
        findings.append("quote expired before comparison date")
    for item_id, needed in required_items.items():
        if item_id not in quoted_quantities:
            findings.append(f"missing mandatory item {item_id}")
        elif quoted_quantities[item_id] < needed:
            findings.append(f"insufficient quantity for {item_id}")
    if not str(quote.get("quality_evidence", "")).strip():
        findings.append("missing quality evidence")
    if not str(quote.get("service_evidence", "")).strip():
        findings.append("missing service evidence")
    if not str(quote.get("source_reference", "")).strip():
        findings.append("missing quote source reference")

    return {
        "quote_id": str(quote["quote_id"]).strip(),
        "supplier_id": str(quote["supplier_id"]).strip(),
        "currency": quote_currency,
        "valid_until": valid_until.isoformat(),
        "total_price": format(total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"),
        "_total": total,
        "_delivery": delivery_days,
        "_quality": quality,
        "_service": service,
        "eligible": not findings,
        "blocking_findings": findings,
        "evidence_references": [
            reference
            for reference in (
                quote.get("source_reference"),
                quote.get("quality_evidence"),
                quote.get("service_evidence"),
            )
            if str(reference or "").strip()
        ],
        "dimension_scores": None,
        "weighted_score": None,
        "rank": None,
    }


def compare_quotes(requirement: dict[str, Any], quotes: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an auditable comparison while preserving every submitted quotation."""
    _required(
        requirement,
        ("request_id", "rfq_id", "currency", "comparison_date", "required_items"),
        "requirement",
    )
    if not isinstance(quotes, list) or not quotes:
        raise ValueError("quotes must be a non-empty list")
    currency = _currency(requirement["currency"])
    comparison_date = _iso_date(requirement["comparison_date"], "comparison_date")
    weights = _weights(requirement)
    required_items = _required_items(requirement)

    rows = [
        _quote_row(quote, required_items, currency, comparison_date) for quote in quotes
    ]
    quote_ids = [row["quote_id"] for row in rows]
    if any(not value for value in quote_ids):
        raise ValueError("quote_id must not be blank")
    if len(set(quote_ids)) != len(quote_ids):
        raise ValueError("duplicate quote_id")

    eligible = [row for row in rows if row["eligible"]]
    if eligible:
        minimum_price = min(row["_total"] for row in eligible)
        minimum_delivery = min(row["_delivery"] for row in eligible)
        for row in eligible:
            scores = {
                "price": Decimal("5") * minimum_price / row["_total"],
                "delivery": Decimal("5") * minimum_delivery / row["_delivery"],
                "quality": row["_quality"],
                "service": row["_service"],
            }
            weighted = sum(
                (scores[name] * weights[name] for name in DEFAULT_WEIGHTS),
                Decimal("0"),
            )
            row["dimension_scores"] = {
                name: format(value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f")
                for name, value in scores.items()
            }
            row["weighted_score"] = format(
                weighted.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"
            )
            row["_weighted"] = weighted

        ordered = sorted(
            eligible,
            key=lambda row: (-row["_weighted"], row["_total"], row["quote_id"]),
        )
        for rank, row in enumerate(ordered, start=1):
            row["rank"] = rank

    for row in rows:
        for internal in ("_total", "_delivery", "_quality", "_service", "_weighted"):
            row.pop(internal, None)

    return {
        "request_id": str(requirement["request_id"]),
        "rfq_id": str(requirement["rfq_id"]),
        "currency": currency,
        "comparison_date": comparison_date.isoformat(),
        "weights": {name: format(value, "f") for name, value in weights.items()},
        "quotes": rows,
        "eligible_quote_count": len(eligible),
        "decision_status": "human_review_required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirement", required=True, type=Path, help="Requirement JSON")
    parser.add_argument("--quotes", required=True, type=Path, help="Quotation array JSON")
    args = parser.parse_args()
    requirement = json.loads(args.requirement.read_text(encoding="utf-8"))
    quotes = json.loads(args.quotes.read_text(encoding="utf-8"))
    print(json.dumps(compare_quotes(requirement, quotes), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
