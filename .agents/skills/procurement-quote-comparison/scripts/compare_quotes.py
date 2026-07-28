#!/usr/bin/env python3
"""Normalize supplier quotations for commercial comparison without supplier scoring."""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
import re
from typing import Any


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
    if not positive and number < 0:
        raise ValueError(f"{field} must be non-negative")
    return number


def _money(value: Decimal) -> str:
    return format(value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f")


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
        ("quote_id", "supplier_id", "currency", "valid_until", "items", "delivery_days"),
        "quote",
    )
    if not isinstance(quote["items"], list) or not quote["items"]:
        raise ValueError("quote items must be a non-empty list")

    quoted_quantities: dict[str, Decimal] = {}
    normalized_items: list[dict[str, str]] = []
    subtotal = Decimal("0")
    for item in quote["items"]:
        _required(item, ("item_id", "quantity", "unit_price"), "quote item")
        item_id = str(item["item_id"]).strip()
        if item_id in quoted_quantities:
            raise ValueError(f"duplicate quote item_id: {item_id}")
        quantity = _decimal(item["quantity"], "quantity", positive=True)
        unit_price = _decimal(item["unit_price"], "unit_price", positive=True)
        line_total = quantity * unit_price
        quoted_quantities[item_id] = quantity
        subtotal += line_total
        normalized_items.append(
            {
                "item_id": item_id,
                "quantity": format(quantity, "f"),
                "unit_price": _money(unit_price),
                "line_total": _money(line_total),
            }
        )

    discount = _decimal(quote.get("discount", "0"), "discount")
    tax = _decimal(quote.get("tax", "0"), "tax")
    freight = _decimal(quote.get("freight", "0"), "freight")
    total = subtotal - discount + tax + freight
    if total <= 0:
        raise ValueError("normalized total must be positive")

    quote_currency = _currency(quote["currency"])
    valid_until = _iso_date(quote["valid_until"], "valid_until")
    delivery_days = _decimal(quote["delivery_days"], "delivery_days")
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
    if not str(quote.get("source_reference", "")).strip():
        findings.append("missing quote source reference")

    return {
        "quote_id": str(quote["quote_id"]).strip(),
        "supplier_id": str(quote["supplier_id"]).strip(),
        "currency": quote_currency,
        "valid_until": valid_until.isoformat(),
        "delivery_days": format(delivery_days, "f"),
        "items": normalized_items,
        "line_subtotal": _money(subtotal),
        "discount": _money(discount),
        "tax": _money(tax),
        "freight": _money(freight),
        "total_price": _money(total),
        "payment_terms": quote.get("payment_terms"),
        "warranty_terms": quote.get("warranty_terms"),
        "eligible": not findings,
        "blocking_findings": findings,
        "evidence_references": [quote["source_reference"]]
        if str(quote.get("source_reference", "")).strip()
        else [],
        "commercial_rank": None,
        "_total": total,
        "_delivery": delivery_days,
    }


def compare_quotes(requirement: dict[str, Any], quotes: list[dict[str, Any]]) -> dict[str, Any]:
    """Return normalized commercial rows while preserving every submitted quotation."""
    _required(
        requirement,
        ("request_id", "rfq_id", "currency", "comparison_date", "required_items"),
        "requirement",
    )
    if not isinstance(quotes, list) or not quotes:
        raise ValueError("quotes must be a non-empty list")
    currency = _currency(requirement["currency"])
    comparison_date = _iso_date(requirement["comparison_date"], "comparison_date")
    required_items = _required_items(requirement)
    rows = [_quote_row(quote, required_items, currency, comparison_date) for quote in quotes]

    quote_ids = [row["quote_id"] for row in rows]
    if any(not value for value in quote_ids):
        raise ValueError("quote_id must not be blank")
    if len(set(quote_ids)) != len(quote_ids):
        raise ValueError("duplicate quote_id")

    eligible = [row for row in rows if row["eligible"]]
    for rank, row in enumerate(
        sorted(eligible, key=lambda item: (item["_total"], item["_delivery"], item["quote_id"])),
        start=1,
    ):
        row["commercial_rank"] = rank

    for row in rows:
        row.pop("_total")
        row.pop("_delivery")

    return {
        "request_id": str(requirement["request_id"]),
        "rfq_id": str(requirement["rfq_id"]),
        "currency": currency,
        "comparison_date": comparison_date.isoformat(),
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
