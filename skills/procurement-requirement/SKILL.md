---
name: procurement-requirement
description: Use when a startup needs to capture, clarify, revise, or prepare a procurement requirement before budget confirmation or supplier sourcing.
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

- Entry point for `procurement-budget-confirmation`.
- Supplies approved specifications to `procurement-supplier-sourcing` and `procurement-quote-comparison`.
- Persists confirmed versions through `procurement-supplier-database` only after authorization.

## Guardrails

- Do not invent demand, specifications, quantities, prices, suppliers, evidence, or approvals.
- Do not design criteria to favor a supplier without a documented business justification.
- Human confirmation is required before freezing the requirement or starting sourcing.

## Example

Convert a request for 20 developer laptops into a CNY requirement with measurable performance, warranty, delivery, security, and acceptance criteria.

## Common Mistakes

- Copying a preferred product name instead of defining the business need
- Mixing mandatory criteria with preferences
- Omitting currency, quantity, version, acceptance evidence, or target date
- Marking an incomplete request ready for sourcing
