---
name: finance-database
description: Use when authorized finance users need to store or query budgets, income, expenses, invoices, payments, receivables, payables, report snapshots, or audit history.
---

# Finance Database

## Overview

Maintain minimum-necessary finance records in an auditable SQLite demonstration database using stable identifiers.

**中文摘要：** 管理部门预算、收入支出、发票、付款、应收应付和财务报表记录，并为每次变更保留审计日志。

## Required Inputs

- Authorized actor, business purpose, and evidence reference
- Entity type, stable entity ID, and validated fields
- Database path and requested query fields
- Data-owner approval for every mutation
- Applicable retention and access policy

## Workflow

1. Read `references/finance_schema.md` and select only the required table and fields.
2. Confirm authorization, purpose, evidence, identity, and query-versus-mutation intent.
3. For local demos, initialize SQLite with `scripts/finance_db.py --database PATH init`.
4. Present the proposed before/after mutation and obtain confirmation.
5. Run the `upsert` command only after confirmation; never modify audit records.
6. Use `query` with an entity ID and explicit comma-separated field allowlist.
7. Verify the returned audit event and report only minimum necessary data.

## Output Contract

Return:

- `operation`, `business_purpose`, `authorized_actor`, and `entity_type`
- stable entity ID and `fields_read` or `before_after_change`
- `evidence_reference`, `audit_event_id`, and timestamp for mutations
- `access_or_retention_notes`

## SkillNet Relationships

- Supports every finance workflow node with confirmed source records.
- Supplies prior invoice keys to `finance-invoice-verification`.
- Supplies approved budgets and posted transactions to `finance-reporting`.

## Guardrails

- Do not store credentials, private keys, raw bank details, identity documents, or unrelated personal data.
- Do not perform silent mutations, broad dumps, unaudited corrections, or destructive audit changes.
- Human confirmation is required before every budget, transaction, invoice, payment, open-item, department, or report mutation.

## Example

After finance approval, store budget `B-1` with its evidence reference, then return the audit event rather than unrelated finance records.

## Common Mistakes

- Using names instead of stable IDs
- Returning full records for a narrow question
- Updating amounts without evidence or actor attribution
- Storing draft or unapproved records as final
