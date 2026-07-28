#!/usr/bin/env python3
"""Maintain a minimum-necessary, audited SQLite technology database."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
from typing import Any


ENTITY_CONFIG = {
    "system": {
        "table": "systems",
        "id_field": "system_id",
        "fields": (
            "system_id",
            "name",
            "owner",
            "criticality",
            "environment_scope",
            "status",
        ),
    },
    "architecture": {
        "table": "architectures",
        "id_field": "architecture_id",
        "fields": (
            "architecture_id",
            "system_id",
            "version",
            "title",
            "status",
            "document_reference",
        ),
    },
    "project": {
        "table": "projects",
        "id_field": "project_id",
        "fields": ("project_id", "system_id", "name", "owner", "status"),
    },
    "code_repository": {
        "table": "code_repositories",
        "id_field": "repository_id",
        "fields": (
            "repository_id",
            "project_id",
            "provider",
            "repository_reference",
            "default_branch",
            "commit_hash",
            "status",
        ),
    },
    "api_document": {
        "table": "api_documents",
        "id_field": "api_document_id",
        "fields": (
            "api_document_id",
            "system_id",
            "version",
            "interface_name",
            "document_reference",
            "status",
        ),
    },
    "test_record": {
        "table": "test_records",
        "id_field": "test_record_id",
        "fields": (
            "test_record_id",
            "system_id",
            "version_id",
            "environment",
            "result",
            "evidence_reference",
            "executed_at",
        ),
    },
    "incident": {
        "table": "incidents",
        "id_field": "incident_id",
        "fields": (
            "incident_id",
            "system_id",
            "version_id",
            "environment",
            "severity",
            "status",
            "opened_at",
            "evidence_reference",
        ),
    },
    "maintenance_record": {
        "table": "maintenance_records",
        "id_field": "maintenance_id",
        "fields": (
            "maintenance_id",
            "system_id",
            "version_id",
            "environment",
            "maintenance_type",
            "status",
            "performed_at",
            "evidence_reference",
        ),
    },
    "system_version": {
        "table": "system_versions",
        "id_field": "version_id",
        "fields": (
            "version_id",
            "system_id",
            "version_label",
            "artifact_digest",
            "environment",
            "status",
            "released_at",
            "evidence_reference",
        ),
    },
}
ENVIRONMENTS = {"local", "development", "test", "staging", "production"}
DIGEST = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
COMMIT_HASH = re.compile(r"^[0-9a-fA-F]{7,64}$")
STATUS_VALUES = {
    "system": {"planned", "active", "maintenance", "retired"},
    "architecture": {"draft", "pending_review", "approved", "superseded"},
    "project": {"planned", "active", "on_hold", "completed", "cancelled"},
    "code_repository": {"active", "read_only", "archived"},
    "api_document": {"draft", "published", "deprecated", "retired"},
    "incident": {"open", "investigating", "mitigated", "resolved", "closed"},
    "maintenance_record": {
        "planned",
        "approved",
        "in_progress",
        "completed",
        "rolled_back",
        "cancelled",
    },
    "system_version": {
        "draft",
        "tested",
        "approved",
        "released",
        "rolled_back",
        "retired",
    },
}
CRITICALITIES = {"low", "medium", "high", "critical"}
TEST_RESULTS = {"passed", "failed", "blocked"}
SEVERITIES = {"low", "medium", "high", "critical"}
VERSION_LINKED_ENTITIES = {"test_record", "incident", "maintenance_record"}


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
        CREATE TABLE IF NOT EXISTS systems (
            system_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            criticality TEXT NOT NULL,
            environment_scope TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS architectures (
            architecture_id TEXT PRIMARY KEY,
            system_id TEXT NOT NULL REFERENCES systems(system_id),
            version TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            document_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            system_id TEXT NOT NULL REFERENCES systems(system_id),
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS code_repositories (
            repository_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(project_id),
            provider TEXT NOT NULL,
            repository_reference TEXT NOT NULL COLLATE NOCASE UNIQUE,
            default_branch TEXT NOT NULL,
            commit_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS system_versions (
            version_id TEXT PRIMARY KEY,
            system_id TEXT NOT NULL REFERENCES systems(system_id),
            version_label TEXT NOT NULL,
            artifact_digest TEXT NOT NULL,
            environment TEXT NOT NULL,
            status TEXT NOT NULL,
            released_at TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (system_id, version_label, environment)
        );

        CREATE TABLE IF NOT EXISTS api_documents (
            api_document_id TEXT PRIMARY KEY,
            system_id TEXT NOT NULL REFERENCES systems(system_id),
            version TEXT NOT NULL,
            interface_name TEXT NOT NULL,
            document_reference TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS test_records (
            test_record_id TEXT PRIMARY KEY,
            system_id TEXT NOT NULL REFERENCES systems(system_id),
            version_id TEXT NOT NULL REFERENCES system_versions(version_id),
            environment TEXT NOT NULL,
            result TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            executed_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            system_id TEXT NOT NULL REFERENCES systems(system_id),
            version_id TEXT NOT NULL REFERENCES system_versions(version_id),
            environment TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            opened_at TEXT NOT NULL,
            evidence_reference TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS maintenance_records (
            maintenance_id TEXT PRIMARY KEY,
            system_id TEXT NOT NULL REFERENCES systems(system_id),
            version_id TEXT NOT NULL REFERENCES system_versions(version_id),
            environment TEXT NOT NULL,
            maintenance_type TEXT NOT NULL,
            status TEXT NOT NULL,
            performed_at TEXT NOT NULL,
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


def _timestamp(value: Any, field: str) -> str:
    raw = str(value).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{field} must be an ISO timestamp") from None
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.isoformat()


def _environment(value: Any) -> str:
    environment = str(value).strip().lower()
    if environment not in ENVIRONMENTS:
        raise ValueError("unsupported environment")
    return environment


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

    if entity_type == "system":
        normalized["criticality"] = str(normalized["criticality"]).lower()
        if normalized["criticality"] not in CRITICALITIES:
            raise ValueError("unsupported system criticality")
    elif entity_type == "code_repository":
        commit_hash = str(normalized["commit_hash"]).lower()
        if not COMMIT_HASH.fullmatch(commit_hash):
            raise ValueError("commit_hash must contain 7 to 64 hexadecimal characters")
        normalized["commit_hash"] = commit_hash
    elif entity_type == "system_version":
        normalized["environment"] = _environment(normalized["environment"])
        digest = str(normalized["artifact_digest"])
        if not DIGEST.fullmatch(digest):
            raise ValueError("artifact_digest must be sha256:<64 hexadecimal characters>")
        normalized["artifact_digest"] = digest.lower()
        normalized["released_at"] = _timestamp(normalized["released_at"], "released_at")
    elif entity_type == "test_record":
        normalized["environment"] = _environment(normalized["environment"])
        normalized["result"] = str(normalized["result"]).lower()
        if normalized["result"] not in TEST_RESULTS:
            raise ValueError("unsupported test result")
        normalized["executed_at"] = _timestamp(normalized["executed_at"], "executed_at")
    elif entity_type == "incident":
        normalized["environment"] = _environment(normalized["environment"])
        normalized["severity"] = str(normalized["severity"]).lower()
        if normalized["severity"] not in SEVERITIES:
            raise ValueError("unsupported incident severity")
        normalized["opened_at"] = _timestamp(normalized["opened_at"], "opened_at")
    elif entity_type == "maintenance_record":
        normalized["environment"] = _environment(normalized["environment"])
        normalized["performed_at"] = _timestamp(normalized["performed_at"], "performed_at")

    if entity_type in STATUS_VALUES:
        normalized["status"] = str(normalized["status"]).lower()
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
            if entity_type == "code_repository":
                duplicate = connection.execute(
                    "SELECT repository_id FROM code_repositories "
                    "WHERE repository_reference = ? COLLATE NOCASE",
                    (normalized["repository_reference"],),
                ).fetchone()
                if duplicate and duplicate["repository_id"] != entity_id:
                    raise ValueError("duplicate repository reference")
            if entity_type == "system_version":
                duplicate = connection.execute(
                    "SELECT version_id FROM system_versions "
                    "WHERE system_id = ? AND version_label = ? AND environment = ?",
                    (
                        normalized["system_id"],
                        normalized["version_label"],
                        normalized["environment"],
                    ),
                ).fetchone()
                if duplicate and duplicate["version_id"] != entity_id:
                    raise ValueError("duplicate system version")
            if entity_type in VERSION_LINKED_ENTITIES:
                version = connection.execute(
                    "SELECT system_id, environment FROM system_versions WHERE version_id = ?",
                    (normalized["version_id"],),
                ).fetchone()
                if version and version["system_id"] != normalized["system_id"]:
                    raise ValueError("record system must match system version")
                if version and version["environment"] != normalized["environment"]:
                    raise ValueError("record environment must match system version")

            insert_columns = (*fields, "created_at", "updated_at")
            insert_values = [normalized[field] for field in fields] + [now, now]
            assignments = ", ".join(
                f"{field} = excluded.{field}" for field in (*fields[1:], "updated_at")
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
        if "code_repositories.repository_reference" in message:
            raise ValueError("duplicate repository reference") from None
        if "system_versions.system_id" in message:
            raise ValueError("duplicate system version") from None
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
        f"SELECT {', '.join(fields)} FROM {config['table']} "
        f"WHERE {config['id_field']} = ?",
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
