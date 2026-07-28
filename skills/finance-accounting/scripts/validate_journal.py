#!/usr/bin/env python3
"""Validate a source-backed draft journal entry before human posting approval."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any


JOURNAL_FIELDS = {
    "journal_id",
    "period",
    "period_status",
    "currency",
    "source_reference",
    "lines",
}
LINE_FIELDS = {"account_code", "debit", "credit", "currency"}


def _require_fields(data: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(field for field in fields if data.get(field) in (None, "", []))
    if missing:
        raise ValueError(f"missing {label} fields: {', '.join(missing)}")


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


def validate_journal(entry: dict[str, Any]) -> dict[str, Any]:
    _require_fields(entry, JOURNAL_FIELDS, "journal")
    if str(entry["period_status"]).strip().lower() != "open":
        raise ValueError("journal period must be open")

    lines = entry["lines"]
    if not isinstance(lines, list) or len(lines) < 2:
        raise ValueError("journal must contain at least two lines")

    journal_currency = str(entry["currency"]).strip().upper()
    debit_total = Decimal("0")
    credit_total = Decimal("0")
    normalized_lines: list[dict[str, str]] = []

    for index, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            raise ValueError(f"line {index} must be an object")
        _require_fields(line, LINE_FIELDS, f"line {index}")
        line_currency = str(line["currency"]).strip().upper()
        if line_currency != journal_currency:
            raise ValueError(f"line {index} currency must match journal currency")

        debit = _money(line["debit"], f"line {index} debit")
        credit = _money(line["credit"], f"line {index} credit")
        if (debit > 0) == (credit > 0):
            raise ValueError(f"line {index} must have exactly one positive side")
        debit_total += debit
        credit_total += credit
        normalized_lines.append(
            {
                "account_code": str(line["account_code"]).strip(),
                "debit": format(debit, "f"),
                "credit": format(credit, "f"),
                "currency": line_currency,
            }
        )

    if debit_total != credit_total:
        raise ValueError(
            f"journal is not balanced: debits {debit_total} != credits {credit_total}"
        )

    return {
        "journal_id": entry["journal_id"],
        "period": entry["period"],
        "currency": journal_currency,
        "source_reference": entry["source_reference"],
        "line_count": len(normalized_lines),
        "lines": normalized_lines,
        "debit_total": format(debit_total, "f"),
        "credit_total": format(credit_total, "f"),
        "balanced": True,
        "validation_status": "passed",
        "posting_status": "draft",
        "decision_status": "human_approval_required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    entry = json.loads(args.entry.read_text(encoding="utf-8"))
    rendered = json.dumps(validate_journal(entry), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
