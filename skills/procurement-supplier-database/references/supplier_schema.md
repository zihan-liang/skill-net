# Supplier Database Schema

## Purpose

This local SQLite schema demonstrates minimum-necessary, audited supplier lifecycle storage. It is not an ERP, vendor portal, contract repository, identity vault, banking system, or system of record.

## Entity Relationships

- `suppliers` is the parent for qualifications, offerings, quotes, contracts, deliveries, and evaluations.
- `contracts` is also the parent for deliveries.
- Stable text IDs supplied by the workflow link records; audit events use an internal integer ID.

## Tables

### suppliers

`supplier_id` (PK), `legal_name`, unique case-insensitive `registration_id`, two-letter `country`, `status`, timestamps.

Statuses: `prospective`, `active`, `suspended`, `inactive`.

### qualifications

`qualification_id` (PK), `supplier_id` (FK), `qualification_type`, `issuer`, `valid_from`, `valid_until`, `status`, `document_reference`, timestamps.

### offerings

`offering_id` (PK), `supplier_id` (FK), `category`, `description`, `status`, timestamps. Use this for the supplier's products and services.

### quotes

`quote_id` (PK), `supplier_id` (FK), `rfq_id`, positive `amount`, three-letter `currency`, `valid_until`, `status`, `source_reference`, timestamps.

### contracts

`contract_id` (PK), `supplier_id` (FK), unique `order_id`, positive `amount`, `currency`, `effective_date`, `end_date`, `status`, `document_reference`, timestamps.

### deliveries

`delivery_id` (PK), `supplier_id` (FK), `contract_id` (FK), `delivered_on`, delivery `status`, `acceptance_status`, `evidence_reference`, timestamps. Supplier must match the referenced contract.

### evaluations

`evaluation_id` (PK), `supplier_id` (FK), `period`, 0–5 `score`, 0–100 `evidence_coverage_percent`, `status`, `evidence_reference`, timestamps. Store only approved or clearly labeled draft evaluation metadata.

### audit_log

Append-only `id`, actor, action, entity type/ID, before/after JSON, evidence reference, business purpose, and UTC timestamp. Database triggers reject update or deletion.

## Mutation Contract

Every `upsert_record` call requires an allowlisted complete record, authorized actor, business purpose, evidence reference, and `confirmed=True`. Validation and SQL execution occur transactionally; a failed record creates neither business data nor an audit event.

## Query Contract

`query_record(connection, entity_type, entity_id, fields)` accepts only fields declared for that entity. Request the smallest field set needed for the stated procurement purpose.

## Excluded Data

Do not store raw bank credentials, identity documents, passwords, tokens, private keys, full contracts, qualification scans, quotations, photos, or other confidential attachments. Store restricted references and access those artifacts only through an authorized system.
