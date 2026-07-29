---
name: finance-budget-check
description: Use when a purchase or expense needs budget balance, funding source, budget account, approval threshold, and availability checks; not for creating the budget or approving the expense.
---

# Finance Budget Check

## Overview

Check whether one proposed commitment is supportable by an approved budget. This finance-owned Skill returns evidence and an approval route, never spending permission.

**中文摘要：** 核对预算余额、资金来源、预算科目、审批阈值和预算可用性；采购可调用，但归属财务，检查结果不等于批准支出。

## Required Inputs

- Request ID/version, department, purpose, amount, currency, and needed date
- Approved budget ID/version, period, account, funding source, allocation, commitments, reservations, and recognized spend
- Funding restrictions, threshold matrix, exception policy, reviewers, and evidence dates

## Workflow

1. Read `assets/budget_check_template.md` and assign a stable `budget_check_id`.
2. Match department, purpose, period, currency, and category to one approved budget account.
3. Calculate availability as allocation minus commitments, reservations, and recognized spend.
4. Verify the funding source permits the proposed use and evidence is current.
5. Identify threshold, transfer, overspend, restricted-fund, and segregation-of-duties conditions.
6. Record each check as passed, failed, missing, or not applicable with a source reference.
7. Return the result and required approval route without changing budget or request status.

## Output Contract

Return budget-check/request IDs, budget version/account, funding source, period/currency, allocation, commitments, reservations, spend, available amount, threshold and restriction findings, missing evidence, approval route, `budget_availability_status`, and `decision_status: human_review_required`.

## SkillNet Relationships

- Blocks `hr-recruitment-publish` when `recruitment_budget_not_approved`.
- Blocks `procurement-purchase-order` when `budget_not_approved`.
- Part of `finance-agent`.
- Follows `finance-budget-planning`.
- Follows `hr-job-requirement` when `recruitment_budget_required`.
- Follows `procurement-requirement`.
- Precedes `finance-expense-request`.
- Precedes `hr-jd-generator` when `recruitment_budget_approved`.
- Precedes `procurement-supplier-search`.

## Approval Controls

- Use stable IDs, minimum necessary fields, authorized sources, and an append-only decision/audit reference.
- Show any proposed record change before an authorized human confirms it.
- Do not invent balances, funding permissions, exchange rates, thresholds, transfers, or approval evidence.
- A positive balance is not approval. Human approval is required for activation, transfer, exception, commitment, and sourcing release.

## Exception Handling

- Block the handoff when evidence is stale, the account or source does not match, currency conversion is unauthorized, or available funds are insufficient.
- List the responsible owner and permitted resolution for every missing item; never silently reclassify or split spend to avoid a threshold.

## Handoff

Pass the budget-check ID, immutable input versions, calculations, restrictions, approval evidence/status, and unresolved issues to `procurement-supplier-search` or the relevant finance reviewer. Do not claim sourcing may start until the human decision is recorded.

## Example

Check a CNY 180,000 laptop requirement against the approved IT-equipment account, funding restrictions, current commitments, and threshold route.

## Common Mistakes

- Using the total department budget instead of the correct account
- Ignoring commitments, reservations, taxes, freight, or evidence dates
- Treating availability as permission to spend
