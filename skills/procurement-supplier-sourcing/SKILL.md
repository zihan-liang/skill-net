---
name: procurement-supplier-sourcing
description: Use when an approved, budget-confirmed procurement requirement needs supplier discovery, qualification checks, competition planning, or a reviewable sourcing shortlist.
---

# Procurement Supplier Sourcing

## Overview

Build a supplier candidate list whose fit, qualifications, evidence quality, conflicts, and exclusions remain visible and traceable.

**中文摘要：** 根据已确认的采购需求寻找并初筛供应商，核验资质、能力、合规证据和利益冲突，形成可审查的候选名单。

## Required Inputs

- Approved requirement/version and budget confirmation
- Category, geography, delivery schedule, mandatory criteria, and sourcing policy
- Existing supplier records, qualification evidence, and restricted-party check references
- Conflict declarations, minimum competition rule, and single-source exception policy

## Workflow

1. Verify the approved requirement and budget check are current and linked.
2. Define neutral search criteria directly from mandatory and preferred requirements.
3. Search authorized internal records and approved external sources; record each source and date.
4. Create stable `supplier_id` values and deduplicate legal entities.
5. Check qualification validity, product/service fit, capacity, geography, compliance evidence, and conflicts.
6. Label missing, expired, self-asserted, or unverified evidence explicitly.
7. Record inclusions and exclusions with criterion-based reasons; document any single-source exception.
8. Draft—but do not send—the shortlist and outreach/RFQ route for human approval.

## Output Contract

Return:

- `request_id`, sourcing scope, search sources/dates, and competition rule
- Candidate rows with `supplier_id`, legal name, fit, qualifications, capacity, and evidence references
- Conflict/compliance findings, exclusions and reasons, evidence gaps, and single-source justification
- Shortlist, approval route, and `outreach_status: not_sent`

## SkillNet Relationships

- Follows `procurement-budget-confirmation`.
- Supplies qualified candidates to `procurement-quote-comparison`.
- Reads/writes authorized supplier records through `procurement-supplier-database`.

## Guardrails

- Do not invent suppliers, capabilities, qualifications, screening results, or approvals.
- Do not exclude solely on unsupported reputation claims or unrelated personal data.
- Human approval is required before outreach, RFQ release, qualification acceptance, or single-source use.

## Example

Build a three-supplier shortlist for 20 laptops using dated registration, authorization, warranty, delivery-capacity, security, and conflict evidence.

## Common Mistakes

- Treating a website claim as verified qualification
- Hiding excluded or single-source candidates
- Using criteria unrelated to the approved requirement
- Contacting suppliers before the shortlist and outreach are approved
