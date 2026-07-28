---
name: procurement-supplier-qualification
description: Use when discovered supplier candidates need qualification, compliance, risk, capacity, and admission checks; not for supplier discovery, quote scoring, award, or post-delivery evaluation.
---

# Procurement Supplier Qualification

## Overview

Verify whether each discovered candidate may enter the sourcing process using dated, attributable evidence and explicit admission criteria.

**中文摘要：** 对候选供应商进行资质、合规、风险、能力和准入检查；不负责搜索、报价评分、选商或履约评价。

## Required Inputs

- Candidate list from `procurement-supplier-search` and approved requirement criteria
- Legal registration, licenses/certifications, beneficial-ownership/conflict declarations, sanctions/compliance references, capacity, and financial/operational risk evidence
- Qualification policy, validity rules, data-access authority, reviewers, and exception route

## Workflow

1. Read `assets/supplier_qualification_checklist.md`; assign `qualification_id` per supplier.
2. Match legal identity and stable supplier ID; resolve duplicate or conflicting identities.
3. Verify each required qualification with issuer/source, scope, status, and validity dates.
4. Assess compliance, conflicts, restricted-party indicators, capacity, continuity, security/privacy, and category risks.
5. Label evidence as verified, self-asserted, expired, missing, or not applicable.
6. Record pass/fail/conditional findings and exception needs without producing a commercial score.
7. Route qualification and admission decisions to conflict-free authorized humans.

## Output Contract

Return qualification/supplier/request IDs, identity match, criterion matrix, evidence dates/references, compliance and risk findings, gaps, exception route, recommendation, and `admission_status: human_review_required`.

## SkillNet Relationships

- Follows `procurement-supplier-search` and precedes `procurement-rfq-generation`.
- Supplies qualification evidence to `procurement-supplier-scoring` and `procurement-supplier-selection`.
- Does not compare prices or publish post-delivery performance ratings.

## Approval Controls

- Store only allowlisted minimum fields; use restricted references instead of scans, identity documents, bank data, secrets, or full attachments.
- Preserve stable IDs, source dates, before/after changes, actor/purpose, and append-only audit evidence for any record update.
- Database status or a calculated result is not proof of qualification. Human approval is required for admission and exceptions.

## Exception Handling

- Block RFQ inclusion for failed mandatory checks, unresolved identity, expired evidence, sanctions concerns, or unapproved exceptions.
- Escalate suspected fraud, conflicts, security/privacy risk, or unavailable verification sources; do not fill gaps with reputation.

## Handoff

Pass only human-admitted suppliers, qualification versions, evidence gaps, conditions, and expiry dates to `procurement-rfq-generation`; retain non-admitted records with reasons.

## Example

Check three laptop suppliers for legal identity, authorization, warranty capacity, compliance, conflicts, and evidence expiry before RFQ inclusion.

## Common Mistakes

- Treating a website or self-declaration as verified evidence
- Turning qualification into a weighted supplier score
- Hiding expired or conditional qualifications
