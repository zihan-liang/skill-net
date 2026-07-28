---
name: finance-invoice-verification
description: Use when an invoice or supplier bill needs arithmetic, supplier, PO/contract, delivery-acceptance, expense, currency, and duplicate checks; not for payment approval or official tax authentication.
---

# Finance Invoice Verification

## Overview

Create an auditable consistency check for invoice data without claiming external tax-authority verification.

**中文摘要：** 核验发票必填字段、金额税额、费用申请匹配度和重复风险，但不代替税务机关验真。

## Required Inputs

- Invoice ID, supplier ID, invoice number, issue date, and currency
- Subtotal, tax, and total from the invoice
- Approved expense ID, supplier, amount, and currency
- Existing normalized supplier/invoice-number keys
- Reviewer, verification source, and deadline

## Workflow

1. Exclude bank credentials and unrelated personal data from the working record.
2. Encode the invoice, expense request, and prior keys as JSON.
3. Run `scripts/verify_invoice.py` to check fields, arithmetic, request matching, and duplicates.
4. Review each discrepancy against the source invoice and approved request.
5. If official authenticity data is available through an authorized channel, record its source separately.
6. Route mismatches, duplicates, missing evidence, and authenticity review to an authorized human.

## Output Contract

Return:

- `invoice_id`, `expense_id`, `invoice_key`, and `calculated_total`
- `arithmetic_status`, `request_match_status`, and `duplicate_status`
- `discrepancies` with code and detail
- `authenticity_status` and source when externally checked
- `decision_status: human_review_required`

## SkillNet Relationships

- Requires outputs from `finance-expense-request` and `finance-expense-review`.
- For procurement invoices, requires accepted delivery evidence from `procurement-delivery-acceptance` and the released PO.
- Precedes `finance-payment-approval` and supports `finance-accounting`.
- Queries only normalized prior invoice keys and minimum authorized fields.

## Approval Controls

- Do not invent invoice fields, authenticity results, or tax treatment.
- Do not describe arithmetic consistency as official invoice authenticity.
- Human approval is required before accepting, rejecting, paying, or recording an invoice.

- Use stable invoice/supplier IDs, minimum fields, allowlisted duplicate keys, restricted invoice references, actor/purpose, and append-only verification evidence.
- A stored invoice status or arithmetic match is not proof of authenticity, acceptance, or payment.

## Exception Handling

- Block payment handoff for duplicates, amount/currency/supplier/PO/acceptance mismatches, missing fields, or unverified authenticity requirements.
- Preserve original invoice data and record corrections as new versions or linked adjustments.

## Handoff

Pass the invoice/expense/PO/delivery IDs, normalized amounts, verification findings, authenticity source/status, evidence references, and human review decision to `finance-payment-approval`; never label it paid.

## Example

Check whether a CNY supplier invoice totaling 106.00 matches a 100.00 subtotal, 6.00 tax, its approved expense, and prior invoice keys.

## Common Mistakes

- Comparing totals without checking currency
- Ignoring supplier and invoice-number duplicates
- Treating missing fields as zero
- Claiming external verification when only local consistency was checked
