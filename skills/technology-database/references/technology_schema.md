# Technology Database Schema

## Purpose

This local SQLite schema demonstrates minimum-necessary, audited technology lifecycle storage. It is not source control, CI/CD, observability, secrets management, ticketing, a live CMDB, or a production system of record.

## Entity Relationships

- `systems` is the parent for architectures, projects, API documents, versions, tests, incidents, and maintenance.
- `projects` is the parent for code repository references.
- `system_versions` is the parent for tests, incidents, and maintenance; linked records must match its system and environment.
- Stable text IDs supplied by the workflow link records; audit events use an internal integer ID.

## Tables

### systems

`system_id` (PK), `name`, `owner`, `criticality`, `environment_scope`, `status`, timestamps.

### architectures

`architecture_id` (PK), `system_id` (FK), `version`, `title`, `status`, `document_reference`, timestamps. Store a restricted design reference, not the full document.

### projects

`project_id` (PK), `system_id` (FK), `name`, `owner`, `status`, timestamps.

### code_repositories

`repository_id` (PK), `project_id` (FK), `provider`, unique case-insensitive `repository_reference`, `default_branch`, hexadecimal `commit_hash`, `status`, timestamps. Store repository and commit references, not source bodies or credentials.

### api_documents

`api_document_id` (PK), `system_id` (FK), `version`, `interface_name`, `document_reference`, `status`, timestamps.

### system_versions

`version_id` (PK), `system_id` (FK), `version_label`, immutable SHA-256 `artifact_digest`, `environment`, `status`, timezone-aware `released_at`, `evidence_reference`, timestamps. System/version/environment identity is unique.

### test_records

`test_record_id` (PK), `system_id` and `version_id` (FKs), `environment`, `result`, `evidence_reference`, timezone-aware `executed_at`, timestamps.

### incidents

`incident_id` (PK), system/version FKs, `environment`, `severity`, `status`, timezone-aware `opened_at`, `evidence_reference`, timestamps.

### maintenance_records

`maintenance_id` (PK), system/version FKs, `environment`, `maintenance_type`, `status`, timezone-aware `performed_at`, `evidence_reference`, timestamps.

### audit_log

Append-only `id`, actor, action, entity type/ID, before/after JSON, evidence reference, business purpose, and UTC timestamp. Database triggers reject update or deletion.

## Mutation Contract

Every `upsert_record` call requires an allowlisted complete record, authorized actor, business purpose, evidence reference, and `confirmed=True`. Validation and SQL execution occur transactionally; a failed record creates neither business data nor an audit event.

## Query Contract

`query_record(connection, entity_type, entity_id, fields)` accepts only fields declared for that entity. Request the smallest field set needed for the stated technology purpose.

## Excluded Data

Do not store source-code bodies, credentials, passwords, tokens, private keys, customer/personal data, full architecture/API documents, raw production logs, database dumps, build artifacts, or binary attachments. Store restricted references and access artifacts only through authorized systems.
