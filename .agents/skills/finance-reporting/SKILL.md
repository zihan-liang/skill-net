---
name: finance-reporting
description: Use when posted finance data must be summarized, compared with budget, reconciled to cash, or prepared as a period management report; not for posting entries or approving payment.
---

# Finance Reporting

## Overview

Generate transparent financial report drafts from approved, source-backed records and expose reconciliation or coverage gaps.

**中文摘要：** 汇总预算、收入、支出、现金、应收和应付数据，生成带勾稽差异与证据覆盖率的财务报告草案。

## Required Inputs

- Report ID, period, currency, purpose, and report owner
- Approved budget records and recognized income/expense transactions
- Opening and actual closing cash balances
- Open or overdue receivable and payable records
- Source references, accounting policy, and review deadline

## Workflow

1. Confirm period boundaries, currency, data cutoff, policy, and approved sources.
2. Export only the required finance records; keep draft items separate from recognized totals.
3. Encode the dataset as JSON and run `scripts/generate_financial_report.py`.
4. Review budget variance, net movement, cash reconciliation, receivables, and payables.
5. Investigate missing sources, unsupported kinds, mixed currencies, and reconciliation differences.
6. Explain material variance using evidence rather than unsupported narrative.
7. Route the draft to an authorized reviewer; publish only the approved version.

## Output Contract

Return:

- `report_id`, `period`, `currency`, and data cutoff
- `budget_total`, `expense_actual`, `budget_variance`, `income_total`, and `expense_total`
- cash movement and `reconciliation_difference`
- `receivables_total`, `payables_total`, and `evidence_coverage`
- `report_status`, `publication_status: draft`, and `decision_status: human_review_required`

## SkillNet Relationships

- Consumes approved budgets from `finance-budget-planning` and posted data from `finance-accounting`.
- Queries only allowlisted minimum source fields and restricted evidence references.
- Records an approved report snapshot only after confirmation, with stable ID/version and append-only audit evidence.

## Approval Controls

- Do not mix currencies or unapproved exchange rates in one total.
- Do not hide missing sources, draft records, or reconciliation gaps.
- Human approval is required for adjustments, period close, report approval, and publication.

- Do not include draft transactions, expose unnecessary records, rewrite approved snapshots, or treat stored status as publication evidence.

## Exception Handling

- Block publication for unreconciled cash, mixed currencies without approved rates, unsupported records, missing sources, or material unexplained variance.
- Return correction needs to accounting through new entries/reversals; never edit source totals inside the report.

## Handoff

Pass the report ID/version, period/cutoff, reconciliations, evidence coverage, exceptions, reviewer decision, and publication status to the authorized report owner; publish only after verified approval.

## Example

Generate a July CNY management report showing budget variance, income, expense, cash reconciliation, and open receivables and payables.

## Common Mistakes

- Counting draft transactions as recognized actuals
- Reporting cash without reconciliation
- Explaining variance without source evidence
- Publishing an unreconciled draft as final
