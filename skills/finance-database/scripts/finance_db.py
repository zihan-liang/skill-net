#!/usr/bin/env python3
"""Maintain a small, privacy-minimized, auditable SQLite finance database."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sqlite3
from typing import Any


ENTITY_CONFIG = {
    "department": {
        "table": "departments",
        "id_field": "department_id",
        "fields": ("department_id", "name", "status"),
    },
    "budget": {
        "table": "budgets",
        "id_field": "budget_id",
        "fields": (
            "budget_id",
            "department_id",
            "period",
            "currency",
            "amount",
            "status",
        ),
    },
    "transaction": {
        "table": "transactions",
        "id_field": "transaction_id",
        "fields": (
            "transaction_id",
            "department_id",
            "kind",
            "amount",
            "currency",
            "occurred_on",
            "status",
            "source_reference",
        ),
    },
    "invoice": {
        "table": "invoices",
        "id_field": "invoice_id",
        "fields": (
            "invoice_id",
            "supplier_id",
            "invoice_number",
            "amount",
            "currency",
            "status",
        ),
    },
    "payment": {
        "table": "payments",
        "id_field": "payment_id",
        "fields": (
            "payment_id",
            "invoice_id",
            "payee_id",
            "amount",
            "currency",
            "status",
        ),
    },
    "open_item": {
        "table": "open_items",
        "id_field": "item_id",
        "fields": (
            "item_id",
            "kind",
            "counterparty_id",
            "amount",
            "currency",
            "due_date",
            "status",
        ),
    },
    "report_snapshot": {
        "table": "report_snapshots",
        "id_field": "report_id",
        "fields": ("report_id", "period", "currency", "status", "payload_json"),
        "input_fields": ("report_id", "period", "currency", "status", "payload"),
    },
}
CURRENCY = re.compile(r"^[A-Z]{3}$")
MONEY_ENTITIES = {"budget", "transaction", "invoice", "payment", "open_item"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect_database(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS departments (
            department_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS budgets (
            budget_id TEXT PRIMARY KEY,
            department_id TEXT NOT NULL REFERENCES departments(department_id),
            period TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            department_id TEXT NOT NULL REFERENCES departments(department_id),
            kind TEXT NOT NULL CHECK (kind IN ('income', 'expense')),
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            occurred_on TEXT NOT NULL,
            status TEXT NOT NULL,
            source_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL COLLATE NOCASE,
            invoice_number TEXT NOT NULL COLLATE NOCASE,
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (supplier_id, invoice_number)
        );

        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL REFERENCES invoices(invoice_id),
            payee_id TEXT NOT NULL,
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS open_items (
            item_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL CHECK (kind IN ('receivable', 'payable')),
            counterparty_id TEXT NOT NULL,
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS report_snapshots (
            report_id TEXT PRIMARY KEY,
            period TEXT NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            before_json TEXT,
            after_json TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            business_purpose TEXT NOT NULL,
            occurred_at TEXT NOT NULL
        );
        """
    )
    connection.commit()


def _money(value: Any) -> str:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("amount must be a valid monetary value") from None
    if not amount.is_finite():
        raise ValueError("amount must be finite")
    if amount < 0:
        raise ValueError("amount must be non-negative")
    return format(amount, "f")


def _config(entity_type: str) -> dict[str, Any]:
    try:
        return ENTITY_CONFIG[entity_type]
    except KeyError:
        raise ValueError(f"unsupported entity type: {entity_type}") from None


def _normalize(entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
    config = _config(entity_type)
    input_fields = tuple(config.get("input_fields", config["fields"]))
    unknown = sorted(set(data) - set(input_fields))
    if unknown:
        raise ValueError(f"unsupported {entity_type} fields: {', '.join(unknown)}")
    missing = sorted(field for field in input_fields if data.get(field) in (None, ""))
    if missing:
        raise ValueError(f"missing {entity_type} fields: {', '.join(missing)}")

    normalized = dict(data)
    if entity_type in MONEY_ENTITIES:
        normalized["amount"] = _money(normalized["amount"])
    if "currency" in normalized:
        currency = str(normalized["currency"]).strip().upper()
        if not CURRENCY.fullmatch(currency):
            raise ValueError("currency must be a three-letter code")
        normalized["currency"] = currency
    if entity_type == "transaction" and normalized["kind"] not in {"income", "expense"}:
        raise ValueError(f"unsupported transaction kind: {normalized['kind']}")
    if entity_type == "open_item" and normalized["kind"] not in {"receivable", "payable"}:
        raise ValueError(f"unsupported open item kind: {normalized['kind']}")
    if entity_type == "invoice":
        normalized["supplier_id"] = str(normalized["supplier_id"]).strip()
        normalized["invoice_number"] = str(normalized["invoice_number"]).strip()
    if entity_type == "report_snapshot":
        if str(normalized["status"]).strip().lower() != "approved":
            raise ValueError("report snapshot status must be approved")
        normalized["status"] = "approved"
        if not isinstance(normalized["payload"], dict):
            raise ValueError("report snapshot payload must be an object")
        normalized["payload_json"] = json.dumps(
            normalized.pop("payload"), ensure_ascii=False, sort_keys=True
        )
    return normalized


def _audit(
    connection: sqlite3.Connection,
    *,
    actor: str,
    entity_type: str,
    entity_id: str,
    before: dict[str, Any] | None,
    after: dict[str, Any],
    evidence_reference: str,
    business_purpose: str,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO audit_log (
            actor, action, entity_type, entity_id, before_json, after_json,
            evidence_reference, business_purpose, occurred_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            actor,
            "update" if before else "insert",
            entity_type,
            entity_id,
            json.dumps(before, ensure_ascii=False, sort_keys=True) if before else None,
            json.dumps(after, ensure_ascii=False, sort_keys=True),
            evidence_reference,
            business_purpose,
            _now(),
        ),
    )
    return int(cursor.lastrowid)


def upsert_record(
    connection: sqlite3.Connection,
    entity_type: str,
    data: dict[str, Any],
    *,
    actor: str,
    business_purpose: str,
    evidence_reference: str,
) -> dict[str, Any]:
    for label, value in (
        ("actor", actor),
        ("business_purpose", business_purpose),
        ("evidence_reference", evidence_reference),
    ):
        if not str(value).strip():
            raise ValueError(f"{label} is required for audited mutations")

    config = _config(entity_type)
    normalized = _normalize(entity_type, data)
    table = config["table"]
    id_field = config["id_field"]
    fields = tuple(config["fields"])
    entity_id = str(normalized[id_field])
    before_row = connection.execute(
        f"SELECT * FROM {table} WHERE {id_field} = ?", (entity_id,)
    ).fetchone()
    before = dict(before_row) if before_row else None
    timestamp = _now()
    created_at = before["created_at"] if before else timestamp
    columns = fields + ("created_at", "updated_at")
    values = tuple(normalized[field] for field in fields) + (created_at, timestamp)
    placeholders = ", ".join("?" for _ in columns)
    updates = ", ".join(
        f"{field} = excluded.{field}" for field in fields if field != id_field
    )
    updates += ", updated_at = excluded.updated_at"

    try:
        with connection:
            connection.execute(
                f"INSERT INTO {table} ({', '.join(columns)}) "
                f"VALUES ({placeholders}) ON CONFLICT({id_field}) DO UPDATE SET {updates}",
                values,
            )
            after = dict(
                connection.execute(
                    f"SELECT * FROM {table} WHERE {id_field} = ?", (entity_id,)
                ).fetchone()
            )
            audit_event_id = _audit(
                connection,
                actor=str(actor).strip(),
                entity_type=entity_type,
                entity_id=entity_id,
                before=before,
                after=after,
                evidence_reference=str(evidence_reference).strip(),
                business_purpose=str(business_purpose).strip(),
            )
    except sqlite3.IntegrityError as exc:
        if entity_type == "invoice" and "invoices.supplier_id" in str(exc):
            raise ValueError("duplicate invoice key") from None
        raise ValueError(f"database constraint failed: {exc}") from None

    return {**after, "audit_event_id": audit_event_id}


def query_record(
    connection: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    fields: list[str],
) -> dict[str, Any]:
    config = _config(entity_type)
    allowed = set(config["fields"]) | {"created_at", "updated_at"}
    requested = list(dict.fromkeys(fields))
    if not requested:
        raise ValueError("at least one query field is required")
    unsupported = sorted(set(requested) - allowed)
    if unsupported:
        raise ValueError(f"unsupported query fields: {', '.join(unsupported)}")
    table = config["table"]
    id_field = config["id_field"]
    row = connection.execute(
        f"SELECT {', '.join(requested)} FROM {table} WHERE {id_field} = ?",
        (entity_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"{entity_type} not found: {entity_id}")
    return dict(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")

    upsert = subparsers.add_parser("upsert")
    upsert.add_argument("--entity", required=True, choices=sorted(ENTITY_CONFIG))
    upsert.add_argument("--data", required=True, type=Path)
    upsert.add_argument("--actor", required=True)
    upsert.add_argument("--purpose", required=True)
    upsert.add_argument("--evidence", required=True)

    query = subparsers.add_parser("query")
    query.add_argument("--entity", required=True, choices=sorted(ENTITY_CONFIG))
    query.add_argument("--id", required=True)
    query.add_argument("--fields", required=True)
    args = parser.parse_args()

    connection = connect_database(args.database)
    initialize_database(connection)
    try:
        if args.command == "init":
            result: dict[str, Any] = {"status": "initialized"}
        elif args.command == "upsert":
            result = upsert_record(
                connection,
                args.entity,
                json.loads(args.data.read_text(encoding="utf-8")),
                actor=args.actor,
                business_purpose=args.purpose,
                evidence_reference=args.evidence,
            )
        else:
            requested_fields = [item.strip() for item in args.fields.split(",") if item.strip()]
            result = query_record(connection, args.entity, args.id, requested_fields)
    finally:
        connection.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
