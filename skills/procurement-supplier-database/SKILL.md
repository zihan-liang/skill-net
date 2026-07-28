---
name: procurement-supplier-database
description: Use when supplier qualifications, products or services, quotation history, contracts, deliveries, evaluations, or minimum-necessary supplier records need controlled storage or retrieval.
---

# Procurement Supplier Database

## Overview

Maintain a local, minimum-necessary supplier lifecycle database with stable identifiers, transactional validation, explicit confirmation, and append-only audit events.

**中文摘要：** 建立供应商数据库，保存供应商资质、产品与服务、历史报价、合同、交付和质量评价；所有写入都需人工确认并保留审计记录。

## Required Inputs

- Operation, entity type, stable ID, minimum fields, and source evidence
- Authorized actor, business purpose, human confirmation, and retention/access policy
- Existing supplier/contract references for child records
- Requested query fields and intended recipient for data minimization

## Workflow

1. Read `references/supplier_schema.md` before choosing fields or relationships.
2. Use `scripts/supplier_db.py init DATABASE` for a local demonstration database.
3. Validate legal identity, dates, amounts, currency, status, score ranges, and foreign keys.
4. Show the proposed insert/update, business purpose, evidence, and affected stable ID.
5. Obtain explicit human confirmation; run `upsert ... --confirmed` only after authorization.
6. Inspect the returned `audit_event_id`; never rewrite or delete audit history.
7. Query only named allowlisted fields and redact unnecessary supplier information.

## Output Contract

Return operation/entity/ID, validated minimum record or query result, validation findings, source reference, actor/purpose, confirmation state, audit event ID for writes, and external-system status `not_connected`.

## SkillNet Relationships

- Supports every procurement skill without replacing their human decisions.
- Stores qualifications and offerings from sourcing, quotes from comparison, approved contract/order metadata, deliveries, and approved evaluations.
- Shares only authorized references with finance workflows.

## Guardrails

- Do not store raw bank credentials, identity documents, secrets, private keys, or full confidential attachments.
- Do not infer approval from database status or write to an external ERP/vendor portal.
- Human confirmation is required for every database mutation, correction, status change, or export.

## Example

After approval, store supplier `SUP-1`, its dated authorization, laptop offering, quotation, contract, accepted delivery, and approved evaluation with seven audit events.

## Common Mistakes

- Creating duplicate supplier identities
- Storing attachments instead of restricted references
- Updating child records without valid supplier/contract links
- Returning entire records when only a few fields were requested
