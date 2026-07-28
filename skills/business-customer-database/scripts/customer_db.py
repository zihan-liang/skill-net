#!/usr/bin/env python3
"""Maintain a minimum-necessary, audited SQLite customer database."""

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
    "customer": {
        "table": "customers",
        "id_field": "customer_id",
        "fields": ("customer_id", "legal_name", "display_name", "segment", "region", "owner", "status"),
        "required": ("customer_id", "legal_name", "display_name", "owner", "status"),
    },
    "contact": {
        "table": "contacts",
        "id_field": "contact_id",
        "fields": ("contact_id", "customer_id", "name", "role", "business_email", "business_phone", "contact_basis", "status"),
        "required": ("contact_id", "customer_id", "name", "role", "business_email", "contact_basis", "status"),
    },
    "requirement": {
        "table": "customer_requirements",
        "id_field": "requirement_id",
        "fields": ("requirement_id", "customer_id", "version", "summary", "status", "evidence_reference"),
        "required": ("requirement_id", "customer_id", "version", "summary", "status", "evidence_reference"),
    },
    "communication": {
        "table": "communication_records",
        "id_field": "communication_id",
        "fields": ("communication_id", "customer_id", "contact_id", "requirement_id", "occurred_at", "channel", "summary", "status", "evidence_reference"),
        "required": ("communication_id", "customer_id", "contact_id", "requirement_id", "occurred_at", "channel", "summary", "status", "evidence_reference"),
    },
    "quotation": {
        "table": "quotation_records",
        "id_field": "quotation_id",
        "fields": ("quotation_id", "customer_id", "opportunity_id", "quotation_number", "version", "currency", "total_amount", "valid_until", "status", "evidence_reference"),
        "required": ("quotation_id", "customer_id", "opportunity_id", "quotation_number", "version", "currency", "total_amount", "valid_until", "status", "evidence_reference"),
    },
    "contract": {
        "table": "contract_records",
        "id_field": "contract_id",
        "fields": ("contract_id", "customer_id", "quotation_id", "contract_reference", "version", "document_digest", "status", "effective_date", "expiry_date", "evidence_reference"),
        "required": ("contract_id", "customer_id", "quotation_id", "contract_reference", "version", "document_digest", "status", "effective_date", "expiry_date", "evidence_reference"),
    },
    "project_progress": {
        "table": "project_progress",
        "id_field": "progress_id",
        "fields": ("progress_id", "customer_id", "contract_id", "project_id", "as_of_date", "completion_percent", "status", "evidence_reference"),
        "required": ("progress_id", "customer_id", "contract_id", "project_id", "as_of_date", "completion_percent", "status", "evidence_reference"),
    },
    "payment": {
        "table": "payment_records",
        "id_field": "payment_id",
        "fields": ("payment_id", "customer_id", "contract_id", "amount", "currency", "due_date", "received_at", "status", "evidence_reference"),
        "required": ("payment_id", "customer_id", "contract_id", "amount", "currency", "due_date", "status", "evidence_reference"),
    },
    "renewal": {
        "table": "renewal_records",
        "id_field": "renewal_id",
        "fields": ("renewal_id", "customer_id", "contract_id", "renewal_date", "proposed_value", "currency", "status", "evidence_reference"),
        "required": ("renewal_id", "customer_id", "contract_id", "renewal_date", "proposed_value", "currency", "status", "evidence_reference"),
    },
}
STATUS_VALUES = {
    "customer": {"lead", "prospect", "active", "inactive", "closed"},
    "contact": {"active", "inactive", "opted_out"},
    "requirement": {"draft", "pending_review", "confirmed", "superseded", "closed"},
    "communication": {"draft", "recorded", "confirmed", "superseded"},
    "quotation": {"draft", "pending_review", "approved", "sent", "accepted", "rejected", "expired", "superseded"},
    "contract": {"draft", "pending_signature", "signed", "active", "expired", "terminated", "superseded"},
    "project_progress": {"planned", "in_progress", "blocked", "delivered", "accepted", "closed"},
    "payment": {"planned", "due", "overdue", "received", "disputed", "waived"},
    "renewal": {"not_due", "due", "pending_review", "offered", "renewed", "not_renewed", "closed"},
}
CHANNELS = {"meeting", "call", "email", "message", "workshop", "other"}
DIGEST = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
CURRENCY = re.compile(r"^[A-Z]{3}$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CONTRACT_LINKED = {"project_progress", "payment", "renewal"}


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
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            legal_name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            segment TEXT NOT NULL,
            region TEXT NOT NULL,
            owner TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS contacts (
            contact_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            business_email TEXT NOT NULL COLLATE NOCASE,
            business_phone TEXT NOT NULL,
            contact_basis TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (customer_id, business_email)
        );
        CREATE TABLE IF NOT EXISTS customer_requirements (
            requirement_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            version TEXT NOT NULL,
            summary TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS communication_records (
            communication_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            contact_id TEXT NOT NULL REFERENCES contacts(contact_id),
            requirement_id TEXT NOT NULL REFERENCES customer_requirements(requirement_id),
            occurred_at TEXT NOT NULL,
            channel TEXT NOT NULL,
            summary TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS quotation_records (
            quotation_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            opportunity_id TEXT NOT NULL,
            quotation_number TEXT NOT NULL COLLATE NOCASE,
            version TEXT NOT NULL,
            currency TEXT NOT NULL,
            total_amount TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (customer_id, quotation_number, version)
        );
        CREATE TABLE IF NOT EXISTS contract_records (
            contract_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            quotation_id TEXT NOT NULL REFERENCES quotation_records(quotation_id),
            contract_reference TEXT NOT NULL COLLATE NOCASE UNIQUE,
            version TEXT NOT NULL,
            document_digest TEXT NOT NULL,
            status TEXT NOT NULL,
            effective_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS project_progress (
            progress_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            contract_id TEXT NOT NULL REFERENCES contract_records(contract_id),
            project_id TEXT NOT NULL,
            as_of_date TEXT NOT NULL,
            completion_percent TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (project_id, as_of_date)
        );
        CREATE TABLE IF NOT EXISTS payment_records (
            payment_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            contract_id TEXT NOT NULL REFERENCES contract_records(contract_id),
            amount TEXT NOT NULL,
            currency TEXT NOT NULL,
            due_date TEXT NOT NULL,
            received_at TEXT NOT NULL,
            status TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS renewal_records (
            renewal_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id),
            contract_id TEXT NOT NULL REFERENCES contract_records(contract_id),
            renewal_date TEXT NOT NULL,
            proposed_value TEXT NOT NULL,
            currency TEXT NOT NULL,
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
        BEFORE UPDATE ON audit_log BEGIN
            SELECT RAISE(ABORT, 'audit_log is append-only');
        END;
        CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
        BEFORE DELETE ON audit_log BEGIN
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


def _date(value: Any, field: str) -> str:
    raw = str(value).strip()
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        raise ValueError(f"{field} must be an ISO date") from None


def _timestamp(value: Any, field: str) -> str:
    raw = str(value).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{field} must be an ISO timestamp") from None
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.isoformat()


def _money(value: Any, field: str, *, positive: bool) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be numeric") from None
    if not number.is_finite():
        raise ValueError(f"{field} must be finite")
    if positive and number <= 0:
        raise ValueError(f"{field} must be positive")
    if not positive and number < 0:
        raise ValueError(f"{field} must be non-negative")
    return f"{number.quantize(Decimal('0.01')):.2f}"


def _currency(value: Any) -> str:
    currency = str(value).strip().upper()
    if not CURRENCY.fullmatch(currency):
        raise ValueError("currency must be a three-letter code")
    return currency


def _normalize(entity_type: str, data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{entity_type} data must be an object")
    config = _config(entity_type)
    fields = config["fields"]
    unknown = sorted(set(data) - set(fields))
    if unknown:
        raise ValueError(f"unsupported {entity_type} fields: {', '.join(unknown)}")
    normalized = {
        field: data.get(field, "").strip() if isinstance(data.get(field, ""), str) else data.get(field, "")
        for field in fields
    }
    missing = sorted(field for field in config["required"] if normalized.get(field) in (None, ""))
    if missing:
        raise ValueError(f"missing {entity_type} fields: {', '.join(missing)}")

    normalized["status"] = str(normalized["status"]).strip().lower()
    if normalized["status"] not in STATUS_VALUES[entity_type]:
        raise ValueError(f"unsupported {entity_type} status")

    if entity_type == "contact":
        email = str(normalized["business_email"]).lower()
        if not EMAIL.fullmatch(email):
            raise ValueError("business_email must be a valid business email")
        normalized["business_email"] = email
    elif entity_type == "communication":
        normalized["occurred_at"] = _timestamp(normalized["occurred_at"], "occurred_at")
        normalized["channel"] = str(normalized["channel"]).lower()
        if normalized["channel"] not in CHANNELS:
            raise ValueError("unsupported communication channel")
    elif entity_type == "quotation":
        normalized["currency"] = _currency(normalized["currency"])
        normalized["total_amount"] = _money(normalized["total_amount"], "total_amount", positive=False)
        normalized["valid_until"] = _date(normalized["valid_until"], "valid_until")
    elif entity_type == "contract":
        digest = str(normalized["document_digest"])
        if not DIGEST.fullmatch(digest):
            raise ValueError("document_digest must be sha256:<64 hexadecimal characters>")
        normalized["document_digest"] = digest.lower()
        normalized["effective_date"] = _date(normalized["effective_date"], "effective_date")
        normalized["expiry_date"] = _date(normalized["expiry_date"], "expiry_date")
        if normalized["expiry_date"] < normalized["effective_date"]:
            raise ValueError("expiry_date must not precede effective_date")
    elif entity_type == "project_progress":
        normalized["as_of_date"] = _date(normalized["as_of_date"], "as_of_date")
        completion = Decimal(_money(normalized["completion_percent"], "completion_percent", positive=False))
        if completion > 100:
            raise ValueError("completion_percent must be between 0 and 100")
        normalized["completion_percent"] = f"{completion:.2f}"
    elif entity_type == "payment":
        normalized["amount"] = _money(normalized["amount"], "amount", positive=True)
        normalized["currency"] = _currency(normalized["currency"])
        normalized["due_date"] = _date(normalized["due_date"], "due_date")
        received_at = str(normalized["received_at"]).strip()
        if received_at:
            normalized["received_at"] = _timestamp(received_at, "received_at")
        if normalized["status"] == "received" and not normalized["received_at"]:
            raise ValueError("received payment requires received_at")
    elif entity_type == "renewal":
        normalized["renewal_date"] = _date(normalized["renewal_date"], "renewal_date")
        normalized["proposed_value"] = _money(normalized["proposed_value"], "proposed_value", positive=False)
        normalized["currency"] = _currency(normalized["currency"])
    return normalized


def _fetch(connection: sqlite3.Connection, entity_type: str, entity_id: str) -> dict[str, Any] | None:
    config = _config(entity_type)
    row = connection.execute(
        f"SELECT {', '.join(config['fields'])} FROM {config['table']} WHERE {config['id_field']} = ?",
        (entity_id,),
    ).fetchone()
    return dict(row) if row else None


def _check_relationships(connection: sqlite3.Connection, entity_type: str, data: dict[str, Any]) -> None:
    if entity_type == "communication":
        contact = connection.execute("SELECT customer_id FROM contacts WHERE contact_id = ?", (data["contact_id"],)).fetchone()
        requirement = connection.execute("SELECT customer_id FROM customer_requirements WHERE requirement_id = ?", (data["requirement_id"],)).fetchone()
        if contact and contact["customer_id"] != data["customer_id"]:
            raise ValueError("communication customer must match contact customer")
        if requirement and requirement["customer_id"] != data["customer_id"]:
            raise ValueError("communication customer must match requirement customer")
    elif entity_type == "contract":
        quotation = connection.execute("SELECT customer_id FROM quotation_records WHERE quotation_id = ?", (data["quotation_id"],)).fetchone()
        if quotation and quotation["customer_id"] != data["customer_id"]:
            raise ValueError("contract customer must match quotation customer")
    elif entity_type in CONTRACT_LINKED:
        contract = connection.execute("SELECT customer_id FROM contract_records WHERE contract_id = ?", (data["contract_id"],)).fetchone()
        if contract and contract["customer_id"] != data["customer_id"]:
            raise ValueError(f"{entity_type} customer must match contract customer")


def _check_duplicates(connection: sqlite3.Connection, entity_type: str, data: dict[str, Any], entity_id: str) -> None:
    if entity_type == "contact":
        row = connection.execute(
            "SELECT contact_id FROM contacts WHERE customer_id = ? AND business_email = ? COLLATE NOCASE",
            (data["customer_id"], data["business_email"]),
        ).fetchone()
        if row and row["contact_id"] != entity_id:
            raise ValueError("duplicate customer contact")
    elif entity_type == "quotation":
        row = connection.execute(
            "SELECT quotation_id FROM quotation_records WHERE customer_id = ? AND quotation_number = ? COLLATE NOCASE AND version = ?",
            (data["customer_id"], data["quotation_number"], data["version"]),
        ).fetchone()
        if row and row["quotation_id"] != entity_id:
            raise ValueError("duplicate quotation version")
    elif entity_type == "contract":
        row = connection.execute(
            "SELECT contract_id FROM contract_records WHERE contract_reference = ? COLLATE NOCASE",
            (data["contract_reference"],),
        ).fetchone()
        if row and row["contract_id"] != entity_id:
            raise ValueError("duplicate contract reference")


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
    audit = {
        "actor": str(actor).strip(),
        "business_purpose": str(business_purpose).strip(),
        "evidence_reference": str(evidence_reference).strip(),
    }
    missing_audit = [name for name, value in audit.items() if not value]
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
            _check_duplicates(connection, entity_type, normalized, entity_id)
            _check_relationships(connection, entity_type, normalized)
            columns = (*fields, "created_at", "updated_at")
            values = [normalized[field] for field in fields] + [now, now]
            assignments = ", ".join(f"{field} = excluded.{field}" for field in (*fields[1:], "updated_at"))
            connection.execute(
                f"INSERT INTO {config['table']} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)}) "
                f"ON CONFLICT({config['id_field']}) DO UPDATE SET {assignments}",
                values,
            )
            after = _fetch(connection, entity_type, entity_id)
            cursor = connection.execute(
                """INSERT INTO audit_log (
                    actor, action, entity_type, entity_id, before_json, after_json,
                    evidence_reference, business_purpose, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    audit["actor"],
                    "update" if before else "insert",
                    entity_type,
                    entity_id,
                    json.dumps(before, ensure_ascii=False, sort_keys=True) if before else None,
                    json.dumps(after, ensure_ascii=False, sort_keys=True),
                    audit["evidence_reference"],
                    audit["business_purpose"],
                    now,
                ),
            )
    except sqlite3.IntegrityError as error:
        message = str(error)
        if "contacts.customer_id" in message:
            raise ValueError("duplicate customer contact") from None
        if "quotation_records.customer_id" in message:
            raise ValueError("duplicate quotation version") from None
        if "contract_records.contract_reference" in message:
            raise ValueError("duplicate contract reference") from None
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
    row = connection.execute(
        f"SELECT {', '.join(fields)} FROM {config['table']} WHERE {config['id_field']} = ?",
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
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            result = query_record(connection, args.entity_type, args.entity_id, args.fields)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
