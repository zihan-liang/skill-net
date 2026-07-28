# Finance Database Schema

Use this schema only for authorized finance purposes. Query stable IDs and return the minimum fields needed.

## Core tables

- `departments`: `department_id`, name, status, timestamps.
- `budgets`: `budget_id`, `department_id`, period, currency, amount, status, timestamps.
- `transactions`: `transaction_id`, department, income/expense kind, amount, currency, accounting date, status, source reference, timestamps.
- `invoices`: `invoice_id`, supplier ID, invoice number, amount, currency, status, timestamps. Supplier ID plus invoice number is unique without case sensitivity.
- `payments`: `payment_id`, invoice ID, payee ID, amount, currency, status, timestamps.
- `open_items`: `item_id`, receivable/payable kind, counterparty ID, amount, currency, due date, status, timestamps.
- `report_snapshots`: `report_id`, period, currency, status, JSON payload, timestamps.
- `audit_log`: actor, action, entity type and ID, before/after JSON, evidence reference, business purpose, and UTC timestamp.

## Record rules

- Use exactly one three-letter currency code per monetary record.
- Store non-negative monetary amounts as decimal strings, not floating-point values.
- Keep income and expense separate in `transactions`.
- Keep receivable and payable separate through the `open_items.kind` field.
- Store only approved report snapshots; retain draft report files outside the database until review.
- Use new versions or reversals for corrections to approved records; never rewrite audit events.

## Access and retention rules

- Require an authorized actor, stated business purpose, and evidence reference for each mutation.
- Return only explicitly requested fields for queries.
- Do not store bank credentials, tokens, private keys, invoice images, identity documents, or unrelated personal data.
- Apply company retention, export, correction, and deletion policy to business records without deleting the audit trail outside authorized policy.
