---
name: business-solution-quotation
description: Use when a qualified opportunity needs a customer solution, proposal scope, pricing model, line-item quotation, discount or tax calculation, approval packet, or quote-version review.
---

# Business Solution and Quotation

## Overview

Translate confirmed requirements into a versioned solution and arithmetically reliable quotation while keeping pricing approval and customer release under human control.

**中文摘要：** 根据已确认需求形成方案与报价草案，核对范围、交付、币种、折扣、税费和有效期；不得擅自定价、承诺或向客户发送。

## Required Inputs

- Customer/opportunity/requirement/solution/quotation IDs, source versions, owner, and evidence
- Customer outcome, scope/exclusions, deliverables, milestones, assumptions, dependencies, acceptance, and support
- Line IDs, descriptions, quantities, unit prices, currency, discount, tax rate, dates, validity, and payment assumptions
- Pricing policy, cost/margin evidence, approval matrix, exception limits, risks, and legal/security review needs

## Workflow

1. Read `assets/solution_quotation_template.md`; preserve confirmed requirement and opportunity traceability.
2. Map every proposed component to an outcome or requirement; state exclusions, assumptions, dependencies, responsibilities, and acceptance.
3. Build uniquely identified quotation lines using one explicit currency and approved commercial inputs.
4. Run `scripts/calculate_quotation.py`; verify subtotal, discount, taxable amount, tax, total, dates, and evidence.
5. Compare price, delivery, capacity, risk, margin, tax assumptions, and policy exceptions; do not hide unsupported items in totals.
6. Version the solution and quotation together; identify changes from the prior customer-visible version.
7. Route solution approval, pricing exceptions, discount, tax review, and external release to authorized humans.

## Output Contract

Return linked IDs/versions, requirement mapping, solution scope, deliverables, assumptions, exclusions, schedule, acceptance, normalized lines, currency, totals, validity, risks, approvals, `quotation_status`, and `external_action`.

## SkillNet Relationships

- Follows `business-opportunity-assessment` and precedes `business-negotiation`.
- Supplies approved commercial terms to `business-contract-signing`.
- Stores confirmed quotation metadata through `business-customer-database`.

## Guardrails

- Do not invent requirements, prices, costs, margin, discounts, tax treatment, approvals, capacity, or delivery commitments.
- Do not send, publish, accept, or represent a draft quotation as approved.
- Human approval is required for scope, price, discount, tax, exception, validity, promise, and customer release.

## Example

Draft a CNY merchant-onboarding solution linked to confirmed requirements and calculate two quotation lines, a 10% discount, and 6% tax for human pricing review.

## Common Mistakes

- Quoting against assumptions instead of confirmed requirements
- Mixing currencies or using floating-point money
- Omitting exclusions, acceptance, dependencies, validity, or version changes
- Sending a mathematically valid but unapproved quotation
