#!/usr/bin/env python3
"""Calculate a draft quotation using Decimal arithmetic."""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
import re
from typing import Any


CENT = Decimal("0.01")


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


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_quotation(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and total a quotation without approving or sending it."""
    if not isinstance(data, dict):
        raise ValueError("quotation data must be an object")
    _required_text(
        data,
        "quotation_id",
        "customer_id",
        "opportunity_id",
        "solution_id",
        "currency",
        "issue_date",
        "valid_until",
        "evidence_reference",
    )

    currency = str(data["currency"]).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("currency must be a three-letter code")
    issue_date = _date(data["issue_date"], "issue_date")
    valid_until = _date(data["valid_until"], "valid_until")
    if valid_until < issue_date:
        raise ValueError("valid_until must not precede issue_date")

    discount_percent = _decimal(data.get("discount_percent", "0"), "discount_percent")
    tax_rate_percent = _decimal(data.get("tax_rate_percent", "0"), "tax_rate_percent")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("discount_percent must be between 0 and 100")
    if tax_rate_percent < 0 or tax_rate_percent > 100:
        raise ValueError("tax_rate_percent must be between 0 and 100")

    lines = data.get("lines")
    if not isinstance(lines, list) or not lines:
        raise ValueError("lines must be a non-empty list")
    normalized_lines: list[dict[str, str]] = []
    line_ids: set[str] = set()
    subtotal = Decimal("0")
    for line in lines:
        if not isinstance(line, dict):
            raise ValueError("quotation line must be an object")
        _required_text(line, "line_id", "description")
        line_id = str(line["line_id"]).strip()
        if line_id in line_ids:
            raise ValueError(f"duplicate line_id: {line_id}")
        line_ids.add(line_id)
        quantity = _decimal(line.get("quantity"), f"line {line_id} quantity")
        unit_price = _decimal(line.get("unit_price"), f"line {line_id} unit_price")
        if quantity <= 0:
            raise ValueError(f"line {line_id} quantity must be positive")
        if unit_price < 0:
            raise ValueError(f"line {line_id} unit_price must be non-negative")
        line_currency = str(line.get("currency", currency)).strip().upper()
        if line_currency != currency:
            raise ValueError(f"line {line_id} currency must match quotation currency")
        amount = _money(quantity * unit_price)
        subtotal += amount
        normalized_lines.append(
            {
                "line_id": line_id,
                "description": str(line["description"]).strip(),
                "quantity": str(quantity),
                "unit_price": f"{_money(unit_price):.2f}",
                "currency": currency,
                "amount": f"{amount:.2f}",
            }
        )

    subtotal = _money(subtotal)
    discount_amount = _money(subtotal * discount_percent / Decimal("100"))
    taxable_amount = _money(subtotal - discount_amount)
    tax_amount = _money(taxable_amount * tax_rate_percent / Decimal("100"))
    total = _money(taxable_amount + tax_amount)
    return {
        "quotation_id": str(data["quotation_id"]).strip(),
        "customer_id": str(data["customer_id"]).strip(),
        "opportunity_id": str(data["opportunity_id"]).strip(),
        "solution_id": str(data["solution_id"]).strip(),
        "currency": currency,
        "issue_date": issue_date.isoformat(),
        "valid_until": valid_until.isoformat(),
        "evidence_reference": str(data["evidence_reference"]).strip(),
        "lines": normalized_lines,
        "subtotal": f"{subtotal:.2f}",
        "discount_percent": f"{discount_percent:.2f}",
        "discount_amount": f"{discount_amount:.2f}",
        "taxable_amount": f"{taxable_amount:.2f}",
        "tax_rate_percent": f"{tax_rate_percent:.2f}",
        "tax_amount": f"{tax_amount:.2f}",
        "total": f"{total:.2f}",
        "quotation_status": "draft_human_review_required",
        "external_action": "not_performed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate a draft quotation without approving or sending it."
    )
    parser.add_argument("--data", required=True, type=Path, help="Quotation JSON")
    args = parser.parse_args()
    payload = json.loads(args.data.read_text(encoding="utf-8"))
    print(json.dumps(calculate_quotation(payload), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
