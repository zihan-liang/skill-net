---
name: business-negotiation
description: Use when a customer proposal, quotation, partnership, scope, price, service level, risk allocation, or contract term needs negotiation preparation, session support, or a traceable negotiation record.
---

# Business Negotiation

## Overview

Prepare and document evidence-based negotiations within an approved mandate while preserving authority, version, and concession boundaries.

**中文摘要：** 明确谈判目标、权限和底线，记录双方立场、让步、交换条件、未决问题与审批；未经授权不得承诺价格、范围或合同条款。

## Required Inputs

- Customer/opportunity/solution/quotation IDs and versions, negotiation purpose, participants, roles, and evidence
- Approved objectives, target position, minimum acceptable position, non-negotiables, tradeable items, and authority limits
- Customer requests, company position, cost/value rationale, alternatives, dependencies, deadlines, and approval matrix
- Legal, privacy, security, finance, delivery, competition, anti-bribery, conflict, and communication constraints

## Workflow

1. Read `assets/negotiation_record_template.md`; assign `negotiation_id` and preserve source versions.
2. Confirm participants, decision authority, approved mandate, escalation route, confidentiality, and note-taking rules.
3. Prepare issues by objective, evidence, opening position, target, limit, alternatives, trade conditions, and owner.
4. During the session, distinguish proposals, questions, conditional exchanges, provisional alignment, rejected items, and binding decisions.
5. Record each concession with giver, receiver, exchanged value, authority/reference, scope, expiry, and dependency.
6. Reconcile scope, price, discount, tax assumptions, schedule, acceptance, service, data/security, liability, IP, exclusivity, termination, and dispute points.
7. Summarize unresolved items, approvals, owners, deadlines, version changes, and proposed next communication.
8. Route commitments, concessions, revised quotation, contract terms, and customer communication to authorized humans.

## Output Contract

Return negotiation/source IDs, mandate, issue/position matrix, session record, concessions, provisional alignments, unresolved items, risks, approvals, owners, next steps, version impact, and `negotiation_status`.

## SkillNet Relationships

- Follows `business-solution-quotation` and precedes `business-contract-signing`.
- Feeds approved changes back to the solution/quotation before contracting.
- Stores authorized communication and negotiation references through `business-customer-database`.

## Guardrails

- Do not invent authority, customer positions, approvals, concessions, alignment, or commitments.
- Do not provide bribes, deceptive claims, collusion, discriminatory terms, or unauthorized confidential information.
- Human approval is required for every binding commitment, exception, concession beyond mandate, revised offer, and external message.

## Example

Prepare a merchant partnership negotiation with an approved discount limit, trade discount only for a longer term, and escalate exclusivity and data-liability requests.

## Common Mistakes

- Negotiating without a documented mandate or walk-away boundary
- Giving concessions without receiving defined value
- Recording provisional alignment as final agreement
- Failing to update quotation or contract versions after changes
