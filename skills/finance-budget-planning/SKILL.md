---
name: finance-budget-planning
description: Use when a department needs a new budget, a budget revision, a forecast baseline, or an approval-ready plan for a defined financial period.
---

# Finance Budget Planning

## Overview

Turn operating assumptions into a versioned departmental budget draft with explicit owners, evidence, risks, and approvals.

**中文摘要：** 制定和修订部门预算，明确预算科目、假设、责任人、风险和审批路线。

## Required Inputs

- Department, budget owner, period, and currency
- Approved strategy, operating targets, and historical actuals
- Revenue, expense, and contingency assumptions with evidence
- Budget line owners, materiality threshold, and approval policy

## Workflow

1. Read `assets/budget_template.md` and assign a stable budget ID and version.
2. Verify the period, department, currency, source dates, and responsible owners.
3. Separate committed amounts from estimates and label every assumption.
4. Build revenue, operating-expense, capital, and contingency lines without netting income against expense.
5. Recompute totals and planned net result; surface unsupported or conflicting figures.
6. Compare material changes with the prior approved version and explain variances.
7. Route the complete draft through department, finance, and final authorization.

## Output Contract

Return:

- `budget_id`, `version`, `department_id`, `period`, and `currency`
- `revenue_lines`, `expense_lines`, `contingency`, and calculated totals
- `assumptions`, `variance_analysis`, `material_risks`, and `missing_information`
- `approval_route`, `evidence_references`, and `approval_status: draft`

## SkillNet Relationships

- Entry node for planned spending and revenue targets.
- Precedes `finance-expense-request` and supports `finance-reporting`.
- Persists approved versions through `finance-database` only after confirmation.

## Guardrails

- Do not invent targets, exchange rates, approvals, or historical actuals.
- Keep currencies separate unless an approved rate and date are supplied.
- Human approval is required before activation, revision, transfer, or release of budget.

## Example

Convert the product team’s quarterly hiring, model-API, and marketing assumptions into a CNY budget draft with version comparison and named approval stages.

## Common Mistakes

- Treating estimates as commitments
- Omitting version, period, currency, or evidence dates
- Hiding overspend by netting revenue and expense
- Marking a draft as approved without authorization evidence
