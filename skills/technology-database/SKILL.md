---
name: technology-database
description: Use when technology architecture, system information, project/code references, API documents, test records, incidents, maintenance, or system versions need controlled storage or retrieval.
---

# Technology Database

## Overview

Maintain a local, minimum-necessary technology lifecycle database with stable identifiers, relationships, validation, explicit confirmation, and append-only audit events.

**中文摘要：** 建立技术数据库，保存技术架构、系统信息、项目代码引用、接口文档、测试记录、故障与维护记录和系统版本；写入需人工确认并保留审计。

## Required Inputs

- Operation, entity type, stable ID, minimum fields, environment, status, and source evidence
- Authorized actor, business purpose, explicit human confirmation, access/retention policy, and intended recipient
- Existing system/project/version references for child records
- Requested query fields and restricted artifact/reference locations

## Workflow

1. Read `references/technology_schema.md` before choosing fields or relationships.
2. Use `scripts/technology_db.py init DATABASE` for a local demonstration database.
3. Validate identifiers, ownership, environment, status, timestamps, artifact/commit identity, uniqueness, and foreign keys.
4. Represent architecture, source, API, test, incident, maintenance, and release artifacts by restricted references—not bodies or secrets.
5. Show the proposed mutation, business purpose, evidence, and affected stable ID.
6. Obtain explicit human confirmation; run `upsert ... --confirmed` only after authorization.
7. Inspect `audit_event_id`; query only named allowlisted fields and redact unnecessary information.

## Output Contract

Return operation/entity/ID, validated minimum record or query result, environment/status, findings, evidence, actor/purpose, confirmation state, audit event ID for writes, and external-system status `not_connected`.

## SkillNet Relationships

- Supports every technology Skill without replacing its human decisions.
- Stores approved architecture/system/project/repository/API metadata, test evidence, incidents, maintenance, and versions.
- Shares only authorized minimum references with HR, finance, and procurement workflows.

## Guardrails

- Do not store source-code bodies, secrets, tokens, private keys, customer/personal data, raw production logs, database dumps, or binary artifacts.
- Do not infer live system state, approval, deployment, recovery, or incident closure from stored status.
- Human confirmation is required for every mutation, correction, status change, export, or external synchronization.

## Example

After approval, store an onboarding system, architecture, project/repository reference, version, API document, test record, incident, and maintenance record with nine audit events.

## Common Mistakes

- Treating the metadata database as source control, secrets storage, or live CMDB
- Creating duplicate repositories or version/environment identities
- Linking tests/incidents to a version from another system or environment
- Returning full records when only system name and status were requested
