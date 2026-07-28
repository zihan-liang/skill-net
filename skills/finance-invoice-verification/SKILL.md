---
name: finance-invoice-verification
description: Use when an invoice, receipt, or supplier billing record must be checked against an approved expense, arithmetic, currency, supplier, or prior invoice records.
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
- Precedes `finance-payment-approval` and supports `finance-accounting`.
- Queries prior invoice keys from `finance-database` using minimum data.

## Guardrails

- Do not invent invoice fields, authenticity results, or tax treatment.
- Do not describe arithmetic consistency as official invoice authenticity.
- Human approval is required before accepting, rejecting, paying, or recording an invoice.

## Example

Check whether a CNY supplier invoice totaling 106.00 matches a 100.00 subtotal, 6.00 tax, its approved expense, and prior invoice keys.

## Common Mistakes

- Comparing totals without checking currency
- Ignoring supplier and invoice-number duplicates
- Treating missing fields as zero
- Claiming external verification when only local consistency was checked
