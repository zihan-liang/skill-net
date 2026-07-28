---
name: procurement-budget-confirmation
description: Use when a procurement requirement needs budget availability, spending-threshold, funding-source, or approval-route confirmation before supplier sourcing.
---

# Procurement Budget Confirmation

## Overview

Create an evidence-backed budget check for one procurement requirement without treating a calculation or recommendation as approval.

**中文摘要：** 核对采购需求对应的预算科目、余额、币种、授权阈值和审批路径；任何预算确认必须由有权限的人员完成。

## Required Inputs

- Approved requirement version, owner, estimated amount, currency, and target date
- Approved budget version, budget line, allocated/committed/spent amounts, and evidence date
- Spending and exception thresholds, approval matrix, and reviewer identities
- Existing commitments, foreign-exchange reference when relevant, and funding restrictions

## Workflow

1. Read `assets/budget_confirmation_template.md`; assign `budget_check_id`.
2. Match the requirement department, category, period, amount, and currency to an approved budget line.
3. Compute available amount as allocation minus approved commitments and recognized spend.
4. Keep currencies separate unless an approved rate, source, and effective date are supplied.
5. Identify threshold, restricted-fund, overspend, transfer, and exception conditions.
6. Check segregation of duties and build the required approval route.
7. Return findings and block sourcing when evidence is missing, expired, or inconsistent.

## Output Contract

Return:

- `budget_check_id`, `request_id`, budget ID/version/line, period, and evidence date
- Requirement amount, allocated/committed/spent/available amounts, and currency
- Threshold findings, restrictions, exceptions, missing evidence, and source references
- Approval route and `confirmation_status: human_review_required`

## SkillNet Relationships

- Follows `procurement-requirement` and precedes `procurement-supplier-sourcing`.
- May read approved budget evidence from `finance-budget-planning` or `finance-database`.
- Stores the confirmed result through `procurement-supplier-database` only after authorization.

## Guardrails

- Do not invent balances, exchange rates, policy thresholds, transfers, or approvals.
- Do not treat a positive balance as permission to spend.
- Human approval is required for confirmation, transfer, exception, or sourcing release.

## Example

Check whether a CNY 180,000 laptop requirement fits the approved IT-equipment line after commitments, then route an over-threshold request to the named approvers.

## Common Mistakes

- Using the total department budget instead of the correct approved line
- Ignoring commitments, taxes, freight, or currency dates
- Allowing the requester to be the only approver
- Marking budget as confirmed without approval evidence
