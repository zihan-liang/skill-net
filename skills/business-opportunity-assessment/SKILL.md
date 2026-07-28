---
name: business-opportunity-assessment
description: Use when a customer need or qualified lead needs an evidence-based opportunity score, pursuit review, pipeline priority recommendation, risk assessment, or qualification decision packet.
---

# Business Opportunity Assessment

## Overview

Evaluate an opportunity consistently and transparently without turning a score into an autonomous pursue, reject, or priority decision.

**中文摘要：** 按战略匹配、需求清晰度、决策人触达、预算准备度、时间准备度和交付匹配度评估商机；评分只供人工决策，不自动判定客户价值。

## Required Inputs

- Customer/opportunity/requirement IDs, owner, source versions, assessment date, and evidence
- Strategic fit, need clarity, authority access, budget readiness, timeline readiness, and delivery fit scores
- Evidence reference for every score, assumptions, dependencies, alternatives, and next-step cost
- Commercial, delivery, privacy, security, legal/compliance, conflict, and reputation risks

## Workflow

1. Preserve customer, requirement, communication, and opportunity traceability.
2. Confirm the opportunity is real, the need is attributable, and unknown budget or authority remains unknown.
3. Score all six dimensions from 0–5 using cited evidence; document rationale separately.
4. Run `scripts/evaluate_opportunity.py` with default or approved custom weights.
5. Review evidence coverage, weighted score, missing evidence, critical risks, assumptions, and disqualifying constraints.
6. Compare pursuit effort, delivery capacity, strategic value, risk, and opportunity cost without fabricating probability or revenue.
7. Route qualification, disqualification, priority, forecast, owner, and next-step decisions to authorized humans.

## Output Contract

Return customer/opportunity IDs, weights, dimension scores/evidence, weighted score, evidence coverage, risks, blocking findings, readiness, recommendation rationale, and `decision_status`.

## SkillNet Relationships

- Follows `business-requirement-communication` and precedes `business-solution-quotation`.
- Sends approved opportunity status and evidence to `business-customer-database`.
- May request delivery-fit evidence from product, technology, finance, or operations skills.

## Guardrails

- Do not invent need, authority, budget, timeline, probability, revenue, evidence, or risk clearance.
- Do not use protected personal traits or unrelated personal data for scoring.
- Human approval is required for qualification, disqualification, priority, forecast, pursuit spend, and customer-facing action.

## Example

Evaluate a merchant onboarding opportunity using six cited scores, flag an unresolved data-processing risk, and return a blocked packet for human review.

## Common Mistakes

- Treating an arithmetic score as a sales decision
- Assigning evidence-free budget or authority scores
- Hiding missing evidence or critical risk behind an average
- Comparing opportunities with unapproved weight changes
