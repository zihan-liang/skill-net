---
name: finance-reporting
description: Use when finance data must be summarized for a period, compared with budget, reconciled to cash, or prepared as an income, expense, receivable, payable, or management report.
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
- Queries source records from `finance-database`.
- Stores an approved report snapshot through `finance-database` after confirmation.

## Guardrails

- Do not mix currencies or unapproved exchange rates in one total.
- Do not hide missing sources, draft records, or reconciliation gaps.
- Human approval is required for adjustments, period close, report approval, and publication.

## Example

Generate a July CNY management report showing budget variance, income, expense, cash reconciliation, and open receivables and payables.

## Common Mistakes

- Counting draft transactions as recognized actuals
- Reporting cash without reconciliation
- Explaining variance without source evidence
- Publishing an unreconciled draft as final
