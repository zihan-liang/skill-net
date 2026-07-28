---
name: finance-payment-approval
description: Use when an approved expense and verified invoice need a payment packet, payee and duplicate checks, approval routing, or release controls; not for executing payment or accounting.
---

# Finance Payment Approval

## Overview

Assemble a controlled payment packet that exposes every prerequisite and keeps approval separate from payment release.

**中文摘要：** 汇总费用、发票、收款方和职责分离证据，形成待授权的付款审批材料。

## Required Inputs

- Approved expense review and invoice-verification output
- Payee ID, verified-detail reference, amount, currency, and due date
- Contract, order, delivery, or milestone evidence
- Approval threshold, requester, reviewer, approver, and releaser
- Prior payment records for duplicate checking

## Workflow

1. Read `assets/payment_approval_template.md` and assign a stable payment ID.
2. Confirm the expense and invoice are approved for the same supplier, amount, and currency.
3. Check contract, delivery, due date, tax, and restricted bank-detail verification references.
4. Search prior payments for duplicate invoice, amount, payee, or source identifiers.
5. Enforce approval thresholds and separate requester, reviewer, approver, and releaser duties.
6. List every passed, failed, and missing prerequisite with evidence.
7. Route the packet for authorization while leaving release and communication statuses unchanged.

## Output Contract

Return:

- `payment_id`, `expense_id`, `invoice_id`, `payee_id`, `amount`, and `currency`
- `verification_checks`, `duplicate_check`, and `segregation_of_duties`
- `blocking_findings`, `approval_route`, and `approval_evidence`
- `approval_status: pending`, `release_status: not_released`, and `communication_status: draft`

## SkillNet Relationships

- Requires `finance-expense-review` and `finance-invoice-verification` outputs.
- Precedes `finance-accounting` after authorized release evidence exists.
- Supplies authorized minimum payment-timeliness evidence to `procurement-supplier-evaluation` after release or settlement is independently verified.
- Records only controlled minimum payment metadata and restricted payee-verification references.

## Approval Controls

- Do not invent payee, bank verification, approval, release, or payment status.
- Do not expose raw bank credentials or send payment instructions.
- Human approval is required for authorization, scheduling, release, cancellation, and status correction.
- Use stable IDs, allowlisted fields, actor/purpose, before/after status evidence, and append-only audit references.
- Approval status is not proof of release, settlement, or payment; never store or expose raw bank credentials.

## Exception Handling

- Block the packet on payee mismatch, duplicate indicators, missing acceptance, failed invoice checks, threshold violation, or segregation conflict.
- Escalate bank-detail changes through an independent authorized verification channel; do not reuse unverified instructions.

## Handoff

Only after verified external release/settlement evidence exists, pass payment/invoice IDs, amount/currency, evidence, dates, approvals, and actual status to `finance-accounting`, and pass the approved minimum timeliness/status reference to `procurement-supplier-evaluation`. Otherwise keep release status `not_released`.

## Example

Prepare a payment packet for approved AI model credits while keeping the requester, finance reviewer, approver, and releaser roles distinct.

## Common Mistakes

- Treating approval as proof of payment
- Reusing bank details without a current verification reference
- Ignoring duplicate invoices or split payments
- Letting one person request, approve, and release funds
