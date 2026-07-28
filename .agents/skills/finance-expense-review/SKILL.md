---
name: finance-expense-review
description: Use when a submitted expense or reimbursement needs policy, evidence, duplicate, conflict, and approval review after a finance budget check; not for recalculating budget availability or approving payment.
---

# Finance Expense Review

## Overview

Evaluate an expense request against approved policy and budget evidence, then prepare an auditable recommendation for an authorized reviewer.

**中文摘要：** 审核费用申请的制度合规性、预算余额、证明材料、重复风险和职责分离情况。

## Required Inputs

- Complete output from `finance-expense-request`
- Applicable expense policy and approval thresholds
- Output from `finance-budget-check` with budget decision evidence
- Reviewer identity, role, and conflict declaration
- Prior request references for duplicate checking

## Workflow

1. Confirm the expense packet, policy, budget-check output, and evidence versions.
2. Check business eligibility, amount threshold, timing, currency, and supporting documents.
3. Verify the budget-check ID/status is current and applicable; do not recompute or override it.
4. Check duplicates, split transactions, supplier conflicts, and unusual urgency.
5. Enforce segregation of duties between requester, reviewer, and payment releaser.
6. Classify every check as passed, failed, missing, or not applicable with evidence.
7. Return approve, reject, or revise recommendations to the authorized decision owner.

## Output Contract

Return:

- `expense_id`, `reviewer`, `policy_version`, and `budget_reference`
- `policy_checks`, `budget_check`, `evidence_check`, and `duplicate_check`
- `conflict_check`, `segregation_of_duties`, and `exceptions`
- `recommendation`, `rationale`, `missing_information`, and `decision_status: human_review_required`

## SkillNet Relationships

- Requires `finance-expense-request` and `finance-budget-check` outputs.
- Precedes `finance-invoice-verification` and `finance-payment-approval`.
- Uses allowlisted minimum records and restricted references for duplicate checks.

## Approval Controls

- Do not infer approval from urgency, manager seniority, or prior similar spending.
- Do not alter the request, policy, budget, or evidence during review.
- Human approval is required for approval, rejection, exception, and budget override.

## Exception Handling

- Return stale/mismatched budget checks, missing policy evidence, duplicates, split transactions, or segregation conflicts to their owners.
- Do not turn missing evidence into compliance or modify the underlying request during review.

## Handoff

Pass the request and budget-check IDs/versions, policy findings, duplicate/conflict checks, exceptions, human decision evidence, and unresolved items to `finance-invoice-verification` when an invoice arrives.

## Example

Review an AI model-credit request against the approved product budget, quote, threshold policy, and requester/reviewer conflict declarations.

## Common Mistakes

- Checking policy but not remaining budget
- Letting the requester be the sole approver
- Treating missing evidence as evidence of compliance
- Approving split or duplicate requests independently
