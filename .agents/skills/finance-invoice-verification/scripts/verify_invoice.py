#!/usr/bin/env python3
"""Validate invoice arithmetic, request consistency, and supplied duplicate keys."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any


INVOICE_FIELDS = {
    "invoice_id",
    "supplier_id",
    "invoice_number",
    "issue_date",
    "currency",
    "subtotal",
    "tax",
    "total",
}
EXPENSE_FIELDS = {"expense_id", "supplier_id", "currency", "amount"}


def _require_fields(data: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(field for field in fields if data.get(field) in (None, ""))
    if missing:
        raise ValueError(f"missing {label} fields: {', '.join(missing)}")


def _money(value: Any, field: str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid monetary amount") from None
    if not amount.is_finite():
        raise ValueError(f"{field} must be a finite monetary amount")
    if amount < 0:
        raise ValueError(f"{field} must be non-negative")
    return amount


def _invoice_key(supplier_id: Any, invoice_number: Any) -> str:
    supplier = str(supplier_id).strip().upper()
    number = str(invoice_number).strip().upper()
    return f"{supplier}|{number}"


def verify_invoice(
    invoice: dict[str, Any],
    expense_request: dict[str, Any],
    existing_keys: list[str],
) -> dict[str, Any]:
    _require_fields(invoice, INVOICE_FIELDS, "invoice")
    _require_fields(expense_request, EXPENSE_FIELDS, "expense request")

    subtotal = _money(invoice["subtotal"], "subtotal")
    tax = _money(invoice["tax"], "tax")
    total = _money(invoice["total"], "total")
    request_amount = _money(expense_request["amount"], "expense request amount")
    discrepancies: list[dict[str, str]] = []

    calculated_total = subtotal + tax
    if calculated_total != total:
        discrepancies.append(
            {
                "code": "invoice_total_mismatch",
                "detail": f"subtotal plus tax is {calculated_total}, invoice total is {total}",
            }
        )

    invoice_currency = str(invoice["currency"]).strip().upper()
    request_currency = str(expense_request["currency"]).strip().upper()
    if invoice_currency != request_currency:
        discrepancies.append(
            {
                "code": "currency_mismatch",
                "detail": f"invoice currency {invoice_currency} differs from request currency {request_currency}",
            }
        )
    if str(invoice["supplier_id"]).strip() != str(expense_request["supplier_id"]).strip():
        discrepancies.append(
            {
                "code": "supplier_mismatch",
                "detail": "invoice supplier differs from expense request supplier",
            }
        )
    if total != request_amount:
        discrepancies.append(
            {
                "code": "amount_mismatch",
                "detail": f"invoice total {total} differs from request amount {request_amount}",
            }
        )

    key = _invoice_key(invoice["supplier_id"], invoice["invoice_number"])
    normalized_existing = {str(item).strip().upper() for item in existing_keys}
    is_duplicate = key in normalized_existing
    if is_duplicate:
        discrepancies.append(
            {
                "code": "duplicate_invoice_key",
                "detail": f"supplier and invoice number key already exists: {key}",
            }
        )

    request_codes = {"currency_mismatch", "supplier_mismatch", "amount_mismatch"}
    return {
        "invoice_id": invoice["invoice_id"],
        "expense_id": expense_request["expense_id"],
        "invoice_key": key,
        "calculated_total": str(calculated_total),
        "arithmetic_status": (
            "failed"
            if any(item["code"] == "invoice_total_mismatch" for item in discrepancies)
            else "passed"
        ),
        "request_match_status": (
            "failed"
            if any(item["code"] in request_codes for item in discrepancies)
            else "passed"
        ),
        "duplicate_status": "potential_duplicate" if is_duplicate else "clear",
        "discrepancies": discrepancies,
        "authenticity_status": "not_verified",
        "decision_status": "human_review_required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invoice", required=True, type=Path)
    parser.add_argument("--expense-request", required=True, type=Path)
    parser.add_argument("--existing-keys", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    invoice = json.loads(args.invoice.read_text(encoding="utf-8"))
    expense_request = json.loads(args.expense_request.read_text(encoding="utf-8"))
    existing_keys = (
        json.loads(args.existing_keys.read_text(encoding="utf-8"))
        if args.existing_keys
        else []
    )
    rendered = json.dumps(
        verify_invoice(invoice, expense_request, existing_keys),
        ensure_ascii=False,
        indent=2,
    )
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
