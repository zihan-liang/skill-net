---
name: procurement-requirement
description: Use when a business need must become a versioned, supplier-neutral procurement requirement before finance budget checking; not for technical specification approval, sourcing, or ordering.
---

# Procurement Requirement

## Overview

Turn a business need into one traceable, supplier-neutral procurement requirement with measurable criteria and explicit evidence gaps.

**中文摘要：** 将业务采购需求整理为可追踪、可比较、供应商中立的需求文件，明确规格、验收标准、证据缺口与审批状态。

## Required Inputs

- Requester, department, owner, business purpose, and source references
- Category, quantity, target date/location, estimated value, and currency
- Functional, technical, service, quality, security, sustainability, and delivery needs
- Existing alternatives, dependencies, risks, and approval policy

## Workflow

1. Read `assets/procurement_request_template.md`; assign `request_id` and version.
2. Verify the business outcome, owner, dates, quantities, currency, and evidence.
3. Convert vague wishes into measurable mandatory or preferred criteria.
4. Define delivery, service-level, documentation, and acceptance criteria.
5. Check whether internal reuse, repair, or an existing contract could meet the need.
6. Remove unjustified supplier-specific wording and surface conflicts or single-source constraints.
7. Recompute the estimated total and route the draft for requirement-owner confirmation.

## Output Contract

Return:

- `request_id`, `version`, requester/owner, department, category, and business purpose
- Items/services with quantity, specifications, mandatory/preferred criteria, and target date
- Estimated amount/currency, acceptance criteria, risks, alternatives, and dependencies
- Evidence references, missing information, approval route, and `status: draft`

## SkillNet Relationships

- Part of `procurement-agent`.
- Enhanced by `technology-feasibility-assessment` when `build_or_buy_decision`.
- Must not run with `finance-expense-request` in the same session when `same_expense`.
- Must not run with `hr-job-requirement` in the same session when `same_capability_gap`.
- Must not run with `technology-development-implementation` in the same session when `same_technology_requirement`.
- Follows `business-solution-quotation` when `external_procurement_required`.
- Follows `hr-offer-generator` when `onboarding_equipment_required`.
- Follows `technology-specification-confirmation` when `external_technology_procurement`.
- Precedes `finance-budget-check`.

## Approval Controls

- Do not invent demand, specifications, quantities, prices, suppliers, evidence, or approvals.
- Do not design criteria to favor a supplier without a documented business justification.
- Human confirmation is required before freezing the requirement or starting sourcing.

## Exception Handling

- Return the request for clarification when quantity, owner, currency, target date, acceptance criteria, or evidence is missing.
- Escalate justified single-source constraints or conflicts; do not embed a preferred supplier as a hidden requirement.

## Handoff

Pass the approved request ID/version, items, estimated amount, business criteria, risks, evidence, and decision status to `finance-budget-check`; send technical needs separately to `technology-specification-confirmation` when applicable.

## Example

Convert a request for 20 developer laptops into a CNY requirement with measurable performance, warranty, delivery, security, and acceptance criteria.

## Common Mistakes

- Copying a preferred product name instead of defining the business need
- Mixing mandatory criteria with preferences
- Omitting currency, quantity, version, acceptance evidence, or target date
- Marking an incomplete request ready for sourcing
