---
name: procurement-supplier-search
description: Use when an approved, budget-cleared procurement requirement needs supplier discovery and a traceable candidate list; not for qualification, scoring, selection, or supplier outreach.
---

# Procurement Supplier Search

## Overview

Search authorized sources and create a broad, supplier-neutral candidate list. Keep discovery separate from qualification decisions.

**中文摘要：** 根据已确认需求搜索潜在供应商并形成候选名单，只负责发现与去重，不负责资质准入、评分或选商。

## Required Inputs

- Approved requirement and `finance-budget-check` decision references
- Category, geography, delivery window, mandatory search criteria, and competition rule
- Authorized internal/external sources, search date, conflict declarations, and owner

## Workflow

1. Read `assets/supplier_search_template.md`; preserve request and budget-check versions.
2. Convert the approved need into neutral search terms without adding qualification judgments.
3. Search authorized sources and record the source, query, date, and coverage.
4. Assign stable provisional supplier IDs and deduplicate legal entities.
5. Record claimed offerings, geography, contact route, and provenance as unverified claims.
6. Explain inclusion, search gaps, concentration risk, and any single-source condition.
7. Draft the candidate list for review without contacting suppliers.

## Output Contract

Return request/budget-check IDs, search scope, sources/dates/queries, candidate IDs and legal names, claimed fit, provenance, duplicates, coverage gaps, competition findings, and `outreach_status: not_sent`.

## SkillNet Relationships

- Follows an authorized result from `finance-budget-check`.
- Passes candidates to `procurement-supplier-qualification`.
- Does not generate an RFQ or evaluate supplier eligibility.

## Approval Controls

- Use minimum necessary supplier data, stable IDs, dated sources, restricted evidence references, and an auditable search record.
- Do not scrape prohibited personal data, invent suppliers or capabilities, or treat web claims as verified.
- Human approval is required before outreach, paid data acquisition, single-source treatment, export, or candidate-list release.

## Exception Handling

- If competition is insufficient, sources conflict, or legal identity is ambiguous, flag the candidate and stop qualification handoff for that record.
- Preserve excluded and duplicate candidates with reasons rather than deleting the evidence trail.

## Handoff

Pass the reviewed candidate list, source dates, unverified claims, conflicts, and gaps to `procurement-supplier-qualification`; do not label any candidate qualified.

## Example

Search approved directories for laptop suppliers and return five deduplicated legal entities with dated provenance and unverified offering claims.

## Common Mistakes

- Combining search with qualification
- Hiding a weak or single-source search
- Contacting candidates before approval
