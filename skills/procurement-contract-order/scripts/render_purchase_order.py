#!/usr/bin/env python3
"""Render an approved but unissued purchase-order draft from a Markdown template."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from pathlib import Path
import re
from typing import Any


REQUIRED_FIELDS = (
    "order_id",
    "contract_id",
    "request_id",
    "selection_id",
    "supplier_id",
    "supplier_legal_name",
    "buyer_name",
    "order_date",
    "delivery_date",
    "delivery_location",
    "currency",
    "payment_terms",
    "acceptance_criteria",
    "selection_approval_reference",
    "order_approval_reference",
    "line_items",
)
PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
TWO_PLACES = Decimal("0.01")


def _positive_decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid number") from None
    if not number.is_finite() or number <= 0:
        raise ValueError(f"{field} must be positive")
    return number


def _safe_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _line_table(items: Any) -> tuple[str, str]:
    if not isinstance(items, list) or not items:
        raise ValueError("line_items must be a non-empty list")
    rows = [
        "| Line | Description | Quantity | Unit | Unit price | Line total |",
        "|---|---|---:|---|---:|---:|",
    ]
    subtotal = Decimal("0")
    seen: set[str] = set()
    for item in items:
        missing = [
            field
            for field in ("line_id", "description", "quantity", "unit", "unit_price")
            if item.get(field) in (None, "")
        ]
        if missing:
            raise ValueError(f"missing line item fields: {', '.join(missing)}")
        line_id = str(item["line_id"]).strip()
        if line_id in seen:
            raise ValueError(f"duplicate line_id: {line_id}")
        seen.add(line_id)
        quantity = _positive_decimal(item["quantity"], "quantity")
        unit_price = _positive_decimal(item["unit_price"], "unit_price")
        line_total = quantity * unit_price
        subtotal += line_total
        rows.append(
            "| {line} | {description} | {quantity} | {unit} | {price} | {total} |".format(
                line=_safe_cell(line_id),
                description=_safe_cell(item["description"]),
                quantity=format(quantity, "f"),
                unit=_safe_cell(item["unit"]),
                price=format(unit_price.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"),
                total=format(line_total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"),
            )
        )
    return "\n".join(rows), format(
        subtotal.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"
    )


def render_purchase_order(template: str, data: dict[str, Any]) -> str:
    """Return a Markdown purchase-order draft; never issue or transmit it."""
    if data.get("selection_approved") is not True:
        raise ValueError("supplier selection approval required")
    if data.get("order_approved") is not True:
        raise ValueError("order release approval required")
    missing = [field for field in REQUIRED_FIELDS if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"missing purchase order fields: {', '.join(missing)}")
    currency = str(data["currency"]).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("currency must be a three-letter code")

    line_items_table, subtotal = _line_table(data["line_items"])
    values = {field: _safe_cell(data[field]) for field in REQUIRED_FIELDS if field != "line_items"}
    values.update(
        {
            "currency": currency,
            "line_items_table": line_items_table,
            "subtotal": subtotal,
        }
    )
    rendered = PLACEHOLDER.sub(
        lambda match: values.get(match.group(1), match.group(0)), template
    )
    unresolved = sorted(set(PLACEHOLDER.findall(rendered)))
    if unresolved:
        raise ValueError(f"unresolved template fields: {', '.join(unresolved)}")
    if "NOT ISSUED" not in rendered.upper():
        raise ValueError("template must visibly mark the order NOT ISSUED")
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path, help="Markdown template")
    parser.add_argument("--data", required=True, type=Path, help="Purchase-order JSON")
    parser.add_argument("--output", type=Path, help="Optional Markdown output path")
    args = parser.parse_args()
    rendered = render_purchase_order(
        args.template.read_text(encoding="utf-8"),
        json.loads(args.data.read_text(encoding="utf-8")),
    )
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
