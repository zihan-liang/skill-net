---
name: finance-expense-request
description: Use when an employee or department needs to request company spending, reimbursement, a supplier purchase, or commitment against an approved budget.
---

# Finance Expense Request

## Overview

Convert an informal spending need into a complete, traceable request packet before review or commitment.

**中文摘要：** 将部门或员工的支出需求整理为包含预算、用途、金额和证据的标准费用申请。

## Required Inputs

- Requester, department, business purpose, and needed-by date
- Supplier or reimbursement context, description, amount, and currency
- Approved budget ID and line reference
- Quote, contract, delivery, or other supporting evidence
- Conflict declaration and review route

## Workflow

1. Read `assets/expense_request_template.md` and assign a stable expense ID.
2. Confirm the business purpose, beneficiary, timing, amount, currency, and supplier.
3. Link the request to an approved budget version and specific budget line.
4. Separate estimates from committed or already-incurred amounts.
5. List supporting evidence by reference; do not copy sensitive payment credentials.
6. Check for a matching prior request, disclosed conflicts, split transactions, and missing facts.
7. Return a draft packet for manager, budget-owner, and finance review.

## Output Contract

Return:

- `expense_id`, `requester`, `department_id`, and `business_purpose`
- `supplier_id`, `amount`, `currency`, `needed_by_date`, and `budget_reference`
- `evidence_references`, `conflict_declaration`, and `duplicate_indicators`
- `missing_information`, `review_route`, and `submission_status: draft`

## SkillNet Relationships

- Requires an approved budget from `finance-budget-planning`.
- Precedes `finance-expense-review` and `finance-invoice-verification`.
- Writes confirmed requests to `finance-database` only after authorization.

## Guardrails

- Do not invent business purpose, supplier details, evidence, budget availability, or urgency.
- Do not store raw bank credentials, identity documents, or unrelated personal data.
- Human confirmation is required before submission, commitment, purchase, or reimbursement.

## Example

Prepare a CNY request for model-API credits, referencing the product team’s approved quarterly budget line and supplier quote.

## Common Mistakes

- Requesting spend without a budget reference
- Splitting one purchase to avoid an approval threshold
- Treating an estimate as an incurred expense
- Omitting currency, evidence, or conflict disclosure
