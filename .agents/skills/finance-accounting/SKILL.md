---
name: finance-accounting
description: Use when an approved financial event needs account classification, draft journal entries, debit-credit validation, source tracing, or posting preparation; not for payment approval or reporting.
---

# Finance Accounting

## Overview

Prepare source-backed journal entries and validate structural accounting invariants before an authorized accountant posts them.

**中文摘要：** 根据已批准业务凭证生成记账草案，并检查借贷平衡、币种、会计期间和来源证据。

## Required Inputs

- Approved payment, receipt, accrual, adjustment, or reversal evidence
- Journal ID, accounting period, period status, and currency
- Approved chart of accounts and accounting policy
- Debit and credit lines with source reference
- Preparer, reviewer, and posting authority

## Workflow

1. Confirm the business event, approved source, amount, currency, and accounting date.
2. Apply the approved accounting policy and chart of accounts; do not guess classification.
3. Create at least two lines with one positive debit or credit per line.
4. Encode the draft as JSON and run `scripts/validate_journal.py`.
5. Resolve unbalanced totals, mixed currencies, missing sources, or closed-period errors.
6. Attach preparer and reviewer evidence while keeping posting status as draft.
7. Route the validated entry to an authorized accountant for posting or rejection.

## Output Contract

Return:

- `journal_id`, `period`, `currency`, and `source_reference`
- normalized `lines`, `line_count`, `debit_total`, and `credit_total`
- `balanced` and `validation_status`
- `accounting_policy_reference`, `review_evidence`, and `posting_status: draft`
- `decision_status: human_approval_required`

## SkillNet Relationships

- Part of `finance-agent`.
- Follows `finance-payment-approval`.
- Precedes `finance-reporting`.

## Approval Controls

- Do not invent account codes, tax treatment, exchange rates, sources, or posting evidence.
- Do not bypass closed periods or overwrite posted entries; prepare reversals or new drafts.
- Human approval is required for account selection, posting, reversal, adjustment, and period close.

- Use minimum allowlisted journal fields and source references; never overwrite posted entries or audit events.
- A balanced draft or stored posting status is not proof that classification or posting was authorized.

## Exception Handling

- Stop on unbalanced lines, closed periods, mixed currency, missing source/approval evidence, duplicate events, or unsupported account classification.
- Correct approved records through authorized reversal or new version, not silent edits.

## Handoff

Pass only posted, evidenced journal IDs/periods/amounts and reconciliation references to `finance-reporting`; retain draft or rejected entries outside recognized totals.

## Example

Validate a CNY draft that debits model-service expense 106.00 and credits bank 106.00 against approved payment evidence.

## Common Mistakes

- Using floats for money
- Allowing one line to contain both debit and credit
- Posting into a closed period
- Treating a balanced entry as automatically correct or authorized
