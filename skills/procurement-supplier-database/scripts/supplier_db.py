#!/usr/bin/env python3
"""Maintain a minimum-necessary, audited SQLite supplier database."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sqlite3
from typing import Any


ENTITY_CONFIG = {
    "supplier": {
        "table": "suppliers",
        "id_field": "supplier_id",
        "fields": (
            "supplier_id",
            "legal_name",
            "registration_id",
            "country",
            "status",
        ),
    },
    "qualification": {
        "table": "qualifications",
        "id_field": "qualification_id",
        "fields": (
            "qualification_id",
            "supplier_id",
            "qualification_type",
            "issuer",
            "valid_from",
            "valid_until",
            "status",
            "document_reference",
        ),
    },
    "offering": {
        "table": "offerings",
        "id_field": "offering_id",
        "fields": ("offering_id", "supplier_id", "category", "description", "status"),
    },
    "quote": {
        "table": "quotes",
        "id_field": "quote_id",
        "fields": (
            "quote_id",
            "supplier_id",
            "rfq_id",
            "amount",
            "currency",
            "valid_until",
            "status",
            "source_reference",
        ),
    },
    "contract": {
        "table": "contracts",
        "id_field": "contract_id",
        "fields": (
            "contract_id",
            "supplier_id",
            "order_id",
            "amount",
            "currency",
            "effective_date",
            "end_date",
            "status",
            "document_reference",
        ),
    },
    "delivery": {
        "table": "deliveries",
        "id_field": "delivery_id",
        "fields": (
            "delivery_id",
            "supplier_id",
            "contract_id",
            "delivered_on",
            "status",
            "acceptance_status",
            "evidence_reference",
        ),
    },
    "evaluation": {
        "table": "evaluations",
        "id_field": "evaluation_id",
        "fields": (
            "evaluation_id",
            "supplier_id",
            "period",
            "score",
            "evidence_coverage_percent",
            "status",
            "evidence_reference",
        ),
    },
}
CURRENCY = re.compile(r"^[A-Z]{3}$")
COUNTRY = re.compile(r"^[A-Z]{2}$")
MONEY_ENTITIES = {"quote", "contract"}
STATUS_VALUES = {
    "supplier": {"prospective", "active", "suspended", "inactive"},
    "qualification": {"pending_review", "valid", "expired", "rejected", "revoked"},
    "offering": {"draft", "active", "inactive"},
    "quote": {"received", "eligible", "ineligible", "selected", "expired", "withdrawn"},
    "contract": {"draft", "pending_review", "active", "completed", "terminated", "void"},
    "delivery": {"expected", "delivered", "partially_delivered", "closed"},
    "evaluation": {"draft", "pending_review", "approved", "superseded"},
}
ACCEPTANCE_VALUES = {
    "pending_review",
    "accepted",
    "accepted_with_exception",
    "quarantined",
    "returned",
    "rejected",
}


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
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY,
            legal_name TEXT NOT NULL,
            registration_id TEXT NOT NULL COLLATE NOCASE UNIQUE,
            country TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS qualifications (
            qualification_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
            qualification_type TEXT NOT NULL,
            issuer TEXT NOT NULL,
            valid_from TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            status TEXT NOT NULL,
            document_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS offerings (
            offering_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS quotes (
            quote_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
            rfq_id TEXT NOT NULL,
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            status TEXT NOT NULL,
            source_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS contracts (
            contract_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
            order_id TEXT NOT NULL UNIQUE,
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            effective_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL,
            document_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS deliveries (
            delivery_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
            contract_id TEXT NOT NULL REFERENCES contracts(contract_id),
            delivered_on TEXT NOT NULL,
            status TEXT NOT NULL,
            acceptance_status TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS evaluations (
            evaluation_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
            period TEXT NOT NULL,
            score TEXT NOT NULL,
            evidence_coverage_percent TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
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

        CREATE TRIGGER IF NOT EXISTS audit_log_no_update
        BEFORE UPDATE ON audit_log
        BEGIN
            SELECT RAISE(ABORT, 'audit_log is append-only');
        END;

        CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
        BEFORE DELETE ON audit_log
        BEGIN
            SELECT RAISE(ABORT, 'audit_log is append-only');
        END;
        """
    )
    connection.commit()


def _config(entity_type: str) -> dict[str, Any]:
    try:
        return ENTITY_CONFIG[entity_type]
    except KeyError:
        raise ValueError(f"unsupported entity type: {entity_type}") from None


def _decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid number") from None
    if not number.is_finite():
        raise ValueError(f"{field} must be finite")
    return number


def _date(value: Any, field: str) -> str:
    try:
        return date.fromisoformat(str(value).strip()).isoformat()
    except ValueError:
        raise ValueError(f"{field} must be an ISO date") from None


def _normalize(entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
    config = _config(entity_type)
    fields = config["fields"]
    unknown = sorted(set(data) - set(fields))
    if unknown:
        raise ValueError(f"unsupported {entity_type} fields: {', '.join(unknown)}")
    missing = sorted(field for field in fields if data.get(field) in (None, ""))
    if missing:
        raise ValueError(f"missing {entity_type} fields: {', '.join(missing)}")

    normalized = {
        field: value.strip() if isinstance(value, str) else value
        for field, value in data.items()
    }
    for field in fields:
        if isinstance(normalized[field], str) and not normalized[field]:
            raise ValueError(f"missing {entity_type} fields: {field}")

    if entity_type == "supplier":
        normalized["registration_id"] = str(normalized["registration_id"]).upper()
        normalized["country"] = str(normalized["country"]).upper()
        if not COUNTRY.fullmatch(normalized["country"]):
            raise ValueError("country must be a two-letter code")

    if entity_type in MONEY_ENTITIES:
        amount = _decimal(normalized["amount"], "amount")
        if amount <= 0:
            raise ValueError("amount must be positive")
        normalized["amount"] = format(amount, "f")
        currency = str(normalized["currency"]).upper()
        if not CURRENCY.fullmatch(currency):
            raise ValueError("currency must be a three-letter code")
        normalized["currency"] = currency

    if entity_type == "qualification":
        normalized["valid_from"] = _date(normalized["valid_from"], "valid_from")
        normalized["valid_until"] = _date(normalized["valid_until"], "valid_until")
        if normalized["valid_until"] < normalized["valid_from"]:
            raise ValueError("valid_until must not precede valid_from")
    elif entity_type == "quote":
        normalized["valid_until"] = _date(normalized["valid_until"], "valid_until")
    elif entity_type == "contract":
        normalized["effective_date"] = _date(normalized["effective_date"], "effective_date")
        normalized["end_date"] = _date(normalized["end_date"], "end_date")
        if normalized["end_date"] < normalized["effective_date"]:
            raise ValueError("end_date must not precede effective_date")
    elif entity_type == "delivery":
        normalized["delivered_on"] = _date(normalized["delivered_on"], "delivered_on")
        if normalized["acceptance_status"] not in ACCEPTANCE_VALUES:
            raise ValueError("unsupported acceptance_status")
    elif entity_type == "evaluation":
        score = _decimal(normalized["score"], "score")
        if score < 0 or score > 5:
            raise ValueError("score must be between 0 and 5")
        coverage = _decimal(
            normalized["evidence_coverage_percent"], "evidence_coverage_percent"
        )
        if coverage < 0 or coverage > 100:
            raise ValueError("evidence_coverage_percent must be between 0 and 100")
        normalized["score"] = format(score, "f")
        normalized["evidence_coverage_percent"] = format(coverage, "f")

    if normalized["status"] not in STATUS_VALUES[entity_type]:
        raise ValueError(f"unsupported {entity_type} status")
    return normalized


def _fetch(
    connection: sqlite3.Connection, entity_type: str, entity_id: str
) -> dict[str, Any] | None:
    config = _config(entity_type)
    columns = ", ".join(config["fields"])
    row = connection.execute(
        f"SELECT {columns} FROM {config['table']} WHERE {config['id_field']} = ?",
        (entity_id,),
    ).fetchone()
    return dict(row) if row else None


def upsert_record(
    connection: sqlite3.Connection,
    entity_type: str,
    data: dict[str, Any],
    *,
    actor: str,
    business_purpose: str,
    evidence_reference: str,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Insert or update one allowlisted record and append its audit event."""
    if confirmed is not True:
        raise ValueError("human confirmation required for database mutation")
    audit_values = {
        "actor": str(actor).strip(),
        "business_purpose": str(business_purpose).strip(),
        "evidence_reference": str(evidence_reference).strip(),
    }
    missing_audit = [name for name, value in audit_values.items() if not value]
    if missing_audit:
        raise ValueError(f"missing audit fields: {', '.join(missing_audit)}")

    config = _config(entity_type)
    normalized = _normalize(entity_type, data)
    entity_id = str(normalized[config["id_field"]])
    fields = config["fields"]
    now = _now()

    try:
        with connection:
            before = _fetch(connection, entity_type, entity_id)
            if entity_type == "supplier":
                duplicate = connection.execute(
                    "SELECT supplier_id FROM suppliers WHERE registration_id = ? COLLATE NOCASE",
                    (normalized["registration_id"],),
                ).fetchone()
                if duplicate and duplicate["supplier_id"] != entity_id:
                    raise ValueError("duplicate supplier registration_id")
            if entity_type == "delivery":
                contract = connection.execute(
                    "SELECT supplier_id FROM contracts WHERE contract_id = ?",
                    (normalized["contract_id"],),
                ).fetchone()
                if contract and contract["supplier_id"] != normalized["supplier_id"]:
                    raise ValueError("delivery supplier must match contract")

            insert_columns = (*fields, "created_at", "updated_at")
            insert_values = [normalized[field] for field in fields] + [
                before.get("created_at", now) if before else now,
                now,
            ]
            assignments = ", ".join(
                f"{field} = excluded.{field}"
                for field in (*fields[1:], "updated_at")
            )
            placeholders = ", ".join("?" for _ in insert_columns)
            connection.execute(
                f"INSERT INTO {config['table']} ({', '.join(insert_columns)}) "
                f"VALUES ({placeholders}) ON CONFLICT({config['id_field']}) "
                f"DO UPDATE SET {assignments}",
                insert_values,
            )
            after = _fetch(connection, entity_type, entity_id)
            cursor = connection.execute(
                """
                INSERT INTO audit_log (
                    actor, action, entity_type, entity_id, before_json, after_json,
                    evidence_reference, business_purpose, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_values["actor"],
                    "update" if before else "insert",
                    entity_type,
                    entity_id,
                    json.dumps(before, ensure_ascii=False, sort_keys=True) if before else None,
                    json.dumps(after, ensure_ascii=False, sort_keys=True),
                    audit_values["evidence_reference"],
                    audit_values["business_purpose"],
                    now,
                ),
            )
    except sqlite3.IntegrityError as error:
        message = str(error)
        if "suppliers.registration_id" in message:
            raise ValueError("duplicate supplier registration_id") from None
        if "contracts.order_id" in message:
            raise ValueError("duplicate contract order_id") from None
        if "FOREIGN KEY" in message:
            raise ValueError("foreign key reference does not exist") from None
        raise ValueError(f"database constraint failed: {message}") from None

    assert after is not None
    return {**after, "audit_event_id": cursor.lastrowid}


def query_record(
    connection: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    fields: list[str],
) -> dict[str, Any] | None:
    """Return only explicitly requested, allowlisted fields for one record."""
    config = _config(entity_type)
    if not fields:
        raise ValueError("at least one query field is required")
    unsupported = sorted(set(fields) - set(config["fields"]))
    if unsupported:
        raise ValueError(f"unsupported query fields: {', '.join(unsupported)}")
    columns = ", ".join(fields)
    row = connection.execute(
        f"SELECT {columns} FROM {config['table']} WHERE {config['id_field']} = ?",
        (str(entity_id).strip(),),
    ).fetchone()
    return dict(row) if row else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("init", help="Initialize a database")
    initialize.add_argument("database", type=Path)

    upsert = subparsers.add_parser("upsert", help="Write one confirmed record")
    upsert.add_argument("database", type=Path)
    upsert.add_argument("entity_type", choices=sorted(ENTITY_CONFIG))
    upsert.add_argument("data", type=Path, help="Record JSON")
    upsert.add_argument("--actor", required=True)
    upsert.add_argument("--business-purpose", required=True)
    upsert.add_argument("--evidence-reference", required=True)
    upsert.add_argument("--confirmed", action="store_true")

    query = subparsers.add_parser("query", help="Query minimum fields")
    query.add_argument("database", type=Path)
    query.add_argument("entity_type", choices=sorted(ENTITY_CONFIG))
    query.add_argument("entity_id")
    query.add_argument("--fields", nargs="+", required=True)

    args = parser.parse_args()
    connection = connect_database(args.database)
    try:
        initialize_database(connection)
        if args.command == "init":
            print(json.dumps({"database": str(args.database), "status": "initialized"}))
        elif args.command == "upsert":
            result = upsert_record(
                connection,
                args.entity_type,
                json.loads(args.data.read_text(encoding="utf-8")),
                actor=args.actor,
                business_purpose=args.business_purpose,
                evidence_reference=args.evidence_reference,
                confirmed=args.confirmed,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            result = query_record(
                connection, args.entity_type, args.entity_id, args.fields
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
