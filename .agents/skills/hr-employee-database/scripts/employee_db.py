#!/usr/bin/env python3
"""Maintain a small auditable SQLite employee database."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


EMPLOYEE_FIELDS = (
    "employee_id",
    "legal_name",
    "preferred_name",
    "department",
    "job_title",
    "manager_id",
    "employment_status",
    "start_date",
    "work_email",
)
REQUIRED_EMPLOYEE_FIELDS = {
    "employee_id",
    "legal_name",
    "department",
    "job_title",
    "employment_status",
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
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            legal_name TEXT NOT NULL,
            preferred_name TEXT,
            department TEXT NOT NULL,
            job_title TEXT NOT NULL,
            manager_id TEXT,
            employment_status TEXT NOT NULL,
            start_date TEXT,
            work_email TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS employee_skills (
            employee_id TEXT NOT NULL REFERENCES employees(employee_id),
            skill_name TEXT NOT NULL,
            proficiency INTEGER NOT NULL CHECK (proficiency BETWEEN 1 AND 5),
            evidence TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (employee_id, skill_name)
        );

        CREATE TABLE IF NOT EXISTS kpi_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL REFERENCES employees(employee_id),
            period TEXT NOT NULL,
            metric TEXT NOT NULL,
            target TEXT,
            actual TEXT,
            status TEXT,
            recorded_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS training_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL REFERENCES employees(employee_id),
            course TEXT NOT NULL,
            status TEXT NOT NULL,
            completed_date TEXT,
            credential TEXT,
            recorded_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            before_json TEXT,
            after_json TEXT,
            occurred_at TEXT NOT NULL
        );
        """
    )
    connection.commit()


def _audit(
    connection: sqlite3.Connection,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> int:
    if not actor.strip():
        raise ValueError("actor is required for audited mutations")
    cursor = connection.execute(
        """
        INSERT INTO audit_log
            (actor, action, entity_type, entity_id, before_json, after_json, occurred_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            actor,
            action,
            entity_type,
            entity_id,
            json.dumps(before, ensure_ascii=False, sort_keys=True) if before else None,
            json.dumps(after, ensure_ascii=False, sort_keys=True) if after else None,
            _now(),
        ),
    )
    return int(cursor.lastrowid)


def _require_employee(connection: sqlite3.Connection, employee_id: str) -> None:
    if not connection.execute(
        "SELECT 1 FROM employees WHERE employee_id = ?", (employee_id,)
    ).fetchone():
        raise ValueError(f"employee not found: {employee_id}")


def upsert_employee(
    connection: sqlite3.Connection, employee: dict[str, Any], *, actor: str
) -> dict[str, Any]:
    unknown = set(employee) - set(EMPLOYEE_FIELDS)
    if unknown:
        raise ValueError(f"unsupported employee fields: {', '.join(sorted(unknown))}")
    missing = [field for field in REQUIRED_EMPLOYEE_FIELDS if not employee.get(field)]
    if missing:
        raise ValueError(f"missing required employee fields: {', '.join(sorted(missing))}")

    employee_id = str(employee["employee_id"])
    row = connection.execute(
        "SELECT * FROM employees WHERE employee_id = ?", (employee_id,)
    ).fetchone()
    before = dict(row) if row else None
    values = {field: None for field in EMPLOYEE_FIELDS}
    if before:
        values.update({field: before.get(field) for field in EMPLOYEE_FIELDS})
    values.update(employee)
    timestamp = _now()
    created_at = before["created_at"] if before else timestamp

    connection.execute(
        """
        INSERT INTO employees (
            employee_id, legal_name, preferred_name, department, job_title,
            manager_id, employment_status, start_date, work_email, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(employee_id) DO UPDATE SET
            legal_name = excluded.legal_name,
            preferred_name = excluded.preferred_name,
            department = excluded.department,
            job_title = excluded.job_title,
            manager_id = excluded.manager_id,
            employment_status = excluded.employment_status,
            start_date = excluded.start_date,
            work_email = excluded.work_email,
            updated_at = excluded.updated_at
        """,
        tuple(values[field] for field in EMPLOYEE_FIELDS)
        + (created_at, timestamp),
    )
    after = dict(
        connection.execute(
            "SELECT * FROM employees WHERE employee_id = ?", (employee_id,)
        ).fetchone()
    )
    audit_event_id = _audit(
        connection,
        actor=actor,
        action="upsert",
        entity_type="employee",
        entity_id=employee_id,
        before=before,
        after=after,
    )
    connection.commit()
    return {**after, "audit_event_id": audit_event_id}


def upsert_skill(
    connection: sqlite3.Connection,
    employee_id: str,
    skill: dict[str, Any],
    *,
    actor: str,
) -> dict[str, Any]:
    skill_name = str(skill.get("skill_name", "")).strip()
    if not skill_name:
        raise ValueError("skill_name is required")
    proficiency = int(skill.get("proficiency", 0))
    if not 1 <= proficiency <= 5:
        raise ValueError("proficiency must be between 1 and 5")
    _require_employee(connection, employee_id)

    row = connection.execute(
        "SELECT * FROM employee_skills WHERE employee_id = ? AND skill_name = ?",
        (employee_id, skill_name),
    ).fetchone()
    before = dict(row) if row else None
    timestamp = _now()
    connection.execute(
        """
        INSERT INTO employee_skills
            (employee_id, skill_name, proficiency, evidence, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(employee_id, skill_name) DO UPDATE SET
            proficiency = excluded.proficiency,
            evidence = excluded.evidence,
            updated_at = excluded.updated_at
        """,
        (employee_id, skill_name, proficiency, skill.get("evidence"), timestamp),
    )
    after = dict(
        connection.execute(
            "SELECT * FROM employee_skills WHERE employee_id = ? AND skill_name = ?",
            (employee_id, skill_name),
        ).fetchone()
    )
    audit_event_id = _audit(
        connection,
        actor=actor,
        action="upsert",
        entity_type="employee_skill",
        entity_id=f"{employee_id}:{skill_name}",
        before=before,
        after=after,
    )
    connection.commit()
    return {**after, "audit_event_id": audit_event_id}


def add_kpi_record(
    connection: sqlite3.Connection,
    employee_id: str,
    record: dict[str, Any],
    *,
    actor: str,
) -> dict[str, Any]:
    _require_employee(connection, employee_id)
    missing = [field for field in ("period", "metric") if not record.get(field)]
    if missing:
        raise ValueError(f"missing required KPI fields: {', '.join(missing)}")
    cursor = connection.execute(
        """
        INSERT INTO kpi_records
            (employee_id, period, metric, target, actual, status, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            employee_id,
            record["period"],
            record["metric"],
            record.get("target"),
            record.get("actual"),
            record.get("status"),
            _now(),
        ),
    )
    record_id = int(cursor.lastrowid)
    after = dict(
        connection.execute("SELECT * FROM kpi_records WHERE id = ?", (record_id,)).fetchone()
    )
    audit_event_id = _audit(
        connection,
        actor=actor,
        action="insert",
        entity_type="kpi_record",
        entity_id=str(record_id),
        before=None,
        after=after,
    )
    connection.commit()
    return {**after, "audit_event_id": audit_event_id}


def add_training_record(
    connection: sqlite3.Connection,
    employee_id: str,
    record: dict[str, Any],
    *,
    actor: str,
) -> dict[str, Any]:
    _require_employee(connection, employee_id)
    missing = [field for field in ("course", "status") if not record.get(field)]
    if missing:
        raise ValueError(f"missing required training fields: {', '.join(missing)}")
    cursor = connection.execute(
        """
        INSERT INTO training_records
            (employee_id, course, status, completed_date, credential, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            employee_id,
            record["course"],
            record["status"],
            record.get("completed_date"),
            record.get("credential"),
            _now(),
        ),
    )
    record_id = int(cursor.lastrowid)
    after = dict(
        connection.execute(
            "SELECT * FROM training_records WHERE id = ?", (record_id,)
        ).fetchone()
    )
    audit_event_id = _audit(
        connection,
        actor=actor,
        action="insert",
        entity_type="training_record",
        entity_id=str(record_id),
        before=None,
        after=after,
    )
    connection.commit()
    return {**after, "audit_event_id": audit_event_id}


def get_employee_summary(
    connection: sqlite3.Connection, employee_id: str
) -> dict[str, Any]:
    employee = connection.execute(
        "SELECT * FROM employees WHERE employee_id = ?", (employee_id,)
    ).fetchone()
    if not employee:
        raise ValueError(f"employee not found: {employee_id}")
    skills = connection.execute(
        "SELECT * FROM employee_skills WHERE employee_id = ? ORDER BY skill_name",
        (employee_id,),
    ).fetchall()
    kpis = connection.execute(
        "SELECT * FROM kpi_records WHERE employee_id = ? ORDER BY period, metric",
        (employee_id,),
    ).fetchall()
    training = connection.execute(
        "SELECT * FROM training_records WHERE employee_id = ? ORDER BY recorded_at",
        (employee_id,),
    ).fetchall()
    return {
        "employee": dict(employee),
        "skills": [dict(row) for row in skills],
        "kpis": [dict(row) for row in kpis],
        "training": [dict(row) for row in training],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")

    employee_parser = subparsers.add_parser("upsert-employee")
    employee_parser.add_argument("--data", required=True, type=Path)
    employee_parser.add_argument("--actor", required=True)

    skill_parser = subparsers.add_parser("upsert-skill")
    skill_parser.add_argument("--employee-id", required=True)
    skill_parser.add_argument("--data", required=True, type=Path)
    skill_parser.add_argument("--actor", required=True)

    kpi_parser = subparsers.add_parser("add-kpi")
    kpi_parser.add_argument("--employee-id", required=True)
    kpi_parser.add_argument("--data", required=True, type=Path)
    kpi_parser.add_argument("--actor", required=True)

    training_parser = subparsers.add_parser("add-training")
    training_parser.add_argument("--employee-id", required=True)
    training_parser.add_argument("--data", required=True, type=Path)
    training_parser.add_argument("--actor", required=True)

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("--employee-id", required=True)
    args = parser.parse_args()

    connection = connect_database(args.database)
    initialize_database(connection)
    if args.command == "init":
        result: dict[str, Any] = {"status": "initialized"}
    elif args.command == "upsert-employee":
        result = upsert_employee(
            connection,
            json.loads(args.data.read_text(encoding="utf-8")),
            actor=args.actor,
        )
    elif args.command == "upsert-skill":
        result = upsert_skill(
            connection,
            args.employee_id,
            json.loads(args.data.read_text(encoding="utf-8")),
            actor=args.actor,
        )
    elif args.command == "add-kpi":
        result = add_kpi_record(
            connection,
            args.employee_id,
            json.loads(args.data.read_text(encoding="utf-8")),
            actor=args.actor,
        )
    elif args.command == "add-training":
        result = add_training_record(
            connection,
            args.employee_id,
            json.loads(args.data.read_text(encoding="utf-8")),
            actor=args.actor,
        )
    else:
        result = get_employee_summary(connection, args.employee_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
