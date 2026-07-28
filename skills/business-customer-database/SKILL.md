---
name: business-customer-database
description: Use when customer profiles, contacts, needs, communications, quotations, contracts, project progress, payment, renewal, or minimum-necessary customer lifecycle records need controlled storage or retrieval.
---

# Business Customer Database

## Overview

Maintain a local, minimum-necessary customer lifecycle database with stable identifiers, relational validation, explicit confirmation, and append-only audit events.

**中文摘要：** 建立客户数据库，保存客户基本信息、联系人、需求、沟通、报价、合同、项目进度、回款和续约记录；所有写入均需人工确认和审计。

## Required Inputs

- Operation, entity type, stable ID, minimum fields, source evidence, and retention/access policy
- Authorized actor, business purpose, explicit human confirmation, and intended recipient
- Existing customer/contact/quotation/contract references for linked records
- Consent or lawful-contact basis for contact data and requested allowlisted query fields

## Workflow

1. Read `references/customer_schema.md` before choosing entity relationships, fields, or statuses.
2. Use `scripts/customer_db.py init DATABASE` for a local demonstration database.
3. Validate stable IDs, customer relationships, dates/timestamps, money/currency, status, contact basis, document digest, and uniqueness.
4. Exclude secrets, identity documents, bank/card data, recordings, message bodies, and full proposal/contract content; store restricted references instead.
5. Show the exact insert/update, business purpose, actor, evidence, and affected record.
6. Obtain explicit human confirmation; run `upsert ... --confirmed` only after authorization.
7. Inspect `audit_event_id`; never update/delete audit history or treat a database value as independent proof.
8. Query only named allowlisted fields and minimize customer/contact data in the response.

## Output Contract

Return operation/entity/ID, validated minimum record or query result, relationship and validation findings, actor/purpose/evidence, confirmation state, audit event ID for writes, and `external_system_status: not_connected`.

## SkillNet Relationships

- Supports all eight business workflow skills without replacing their human decisions.
- Stores customer/contact/need/communication data before commercial records, then quotation, contract, project, payment, and renewal metadata.
- Shares only approved minimum references with finance, legal, product, technology, or operations skills.

## Guardrails

- Do not store authentication secrets, IDs, bank/card data, recordings, full messages, full proposals/contracts, or unrelated personal data.
- Do not infer consent, approval, signature, delivery, acceptance, payment, or renewal from status alone.
- Human confirmation is required for every mutation, correction, status change, export, merge, or deletion request.

## Example

After approval, store a fictional customer, business contact, confirmed need, communication, quotation, signed-contract reference, project progress, payment status, and renewal review with nine audit events.

## Common Mistakes

- Duplicating contacts, quotation versions, or contract references
- Linking a contract or project record to the wrong customer
- Storing full content instead of restricted evidence references
- Returning entire contact records when only status is needed
