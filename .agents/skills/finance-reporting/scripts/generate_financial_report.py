#!/usr/bin/env python3
"""Generate a source-covered draft finance summary with cash reconciliation."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any


REPORT_FIELDS = {
    "report_id",
    "period",
    "currency",
    "opening_cash",
    "closing_cash",
    "budgets",
    "transactions",
    "receivables",
    "payables",
}
RECOGNIZED_TRANSACTION_STATUSES = {"approved", "posted", "paid"}
OPEN_ITEM_STATUSES = {"open", "overdue"}
CENT = Decimal("0.01")


def _money(value: Any, label: str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label} must be a valid monetary amount") from None
    if not amount.is_finite():
        raise ValueError(f"{label} must be finite")
    if amount < 0:
        raise ValueError(f"{label} must be non-negative")
    return amount


def _format_money(value: Decimal) -> str:
    return format(value.quantize(CENT), "f")


def _validate_collection(
    records: Any,
    label: str,
    id_field: str,
    currency: str,
) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError(f"{label} must be a list")
    validated: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or not record.get(id_field):
            raise ValueError(f"{label} item must include {id_field}")
        item_id = str(record[id_field])
        item_currency = str(record.get("currency", "")).strip().upper()
        if item_currency != currency:
            raise ValueError(f"{label} item {item_id} currency must be {currency}")
        _money(record.get("amount"), f"{label} item {item_id} amount")
        validated.append(record)
    return validated


def generate_report(data: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(field for field in REPORT_FIELDS if data.get(field) in (None, ""))
    if missing:
        raise ValueError(f"missing report fields: {', '.join(missing)}")

    currency = str(data["currency"]).strip().upper()
    opening_cash = _money(data["opening_cash"], "opening_cash")
    closing_cash = _money(data["closing_cash"], "closing_cash")
    budgets = _validate_collection(data["budgets"], "budgets", "budget_id", currency)
    transactions = _validate_collection(
        data["transactions"], "transactions", "transaction_id", currency
    )
    receivables = _validate_collection(
        data["receivables"], "receivables", "item_id", currency
    )
    payables = _validate_collection(data["payables"], "payables", "item_id", currency)

    recognized_budgets = [
        item for item in budgets if str(item.get("status", "")).lower() == "approved"
    ]
    recognized_transactions = [
        item
        for item in transactions
        if str(item.get("status", "")).lower() in RECOGNIZED_TRANSACTION_STATUSES
    ]
    open_receivables = [
        item
        for item in receivables
        if str(item.get("status", "")).lower() in OPEN_ITEM_STATUSES
    ]
    open_payables = [
        item
        for item in payables
        if str(item.get("status", "")).lower() in OPEN_ITEM_STATUSES
    ]

    def total(records: list[dict[str, Any]]) -> Decimal:
        return sum((_money(item["amount"], "amount") for item in records), Decimal("0"))

    budget_total = total(recognized_budgets)
    income_total = total(
        [item for item in recognized_transactions if item.get("kind") == "income"]
    )
    expense_total = total(
        [item for item in recognized_transactions if item.get("kind") == "expense"]
    )
    invalid_kinds = sorted(
        {
            str(item.get("kind"))
            for item in recognized_transactions
            if item.get("kind") not in {"income", "expense"}
        }
    )
    if invalid_kinds:
        raise ValueError(f"unsupported transaction kinds: {', '.join(invalid_kinds)}")

    net_movement = income_total - expense_total
    expected_closing = opening_cash + net_movement
    reconciliation_difference = closing_cash - expected_closing
    relevant_records = (
        recognized_budgets
        + recognized_transactions
        + open_receivables
        + open_payables
    )
    evidenced = sum(bool(str(item.get("source_reference", "")).strip()) for item in relevant_records)
    evidence_coverage = round(evidenced / len(relevant_records), 2) if relevant_records else 0.0

    if reconciliation_difference != 0:
        status = "draft_unreconciled"
    elif evidence_coverage < 1.0:
        status = "draft_incomplete"
    else:
        status = "ready_for_review"

    return {
        "report_id": data["report_id"],
        "period": data["period"],
        "currency": currency,
        "budget_total": _format_money(budget_total),
        "expense_actual": _format_money(expense_total),
        "budget_variance": _format_money(budget_total - expense_total),
        "income_total": _format_money(income_total),
        "expense_total": _format_money(expense_total),
        "net_movement": _format_money(net_movement),
        "opening_cash": _format_money(opening_cash),
        "expected_closing_cash": _format_money(expected_closing),
        "actual_closing_cash": _format_money(closing_cash),
        "reconciliation_difference": _format_money(reconciliation_difference),
        "receivables_total": _format_money(total(open_receivables)),
        "payables_total": _format_money(total(open_payables)),
        "evidence_coverage": evidence_coverage,
        "report_status": status,
        "publication_status": "draft",
        "decision_status": "human_review_required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.data.read_text(encoding="utf-8"))
    rendered = json.dumps(generate_report(data), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
