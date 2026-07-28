---
name: business-requirement-communication
description: Use when a customer or partner discovery meeting, needs interview, requirement clarification, stakeholder conversation, or follow-up confirmation needs preparation or documentation.
---

# Business Requirement Communication

## Overview

Turn customer conversations into traceable requirements while separating direct statements, interpretations, assumptions, and unresolved questions.

**中文摘要：** 准备并记录客户需求沟通，区分客户原话、内部理解、假设和已确认需求，形成责任明确的下一步；不得虚构沟通或替客户确认。

## Required Inputs

- Lead/customer/contact IDs, conversation purpose, authorized participants, channel, time, and consent or recording policy
- Known context, customer statements, business goal, users, current process, pain points, and desired outcomes
- Scope, constraints, decision process, success measures, budget/timeline signals, dependencies, and risks
- Evidence references, confidentiality/data classification, owner, and requested next step

## Workflow

1. Read `assets/requirement_communication_template.md`; assign `communication_id` and `requirement_id` when appropriate.
2. Prepare open questions around outcome, users, current state, pain, priority, scope, success, constraints, authority, budget, timeline, and alternatives.
3. Confirm participant identity, meeting purpose, permitted data handling, and any confidentiality or recording restriction.
4. During documentation, label each item as customer statement, observed fact, internal interpretation, assumption, or open question.
5. Convert supported statements into measurable requirements and acceptance signals; preserve source and version.
6. Summarize agreements, disagreements, exclusions, risks, missing evidence, owners, dates, and proposed next steps.
7. Send nothing and mark nothing confirmed until an authorized human reviews the record and customer-confirmation route.

## Output Contract

Return customer/contact/communication/requirement IDs, context, attributed notes, requirement matrix, assumptions, open questions, success measures, decision process, risks, owners, next steps, evidence, and `confirmation_status`.

## SkillNet Relationships

- Follows `business-customer-lead` and precedes `business-opportunity-assessment`.
- Supplies confirmed requirements to `business-solution-quotation`.
- Stores approved minimum records through `business-customer-database`.

## Guardrails

- Do not invent attendance, statements, agreement, budget, authority, urgency, or customer confirmation.
- Do not record calls, expose sensitive data, or contact participants outside explicit authority and policy.
- Human approval is required before sending minutes, confirming requirements, changing scope, or writing customer data.

## Example

Prepare a discovery guide for restaurant-group onboarding, then document stated goals, success measures, timeline signals, unknown budget, data concerns, and customer-confirmation actions.

## Common Mistakes

- Writing assumptions as customer requirements
- Asking only feature questions and missing outcomes or decision process
- Omitting attribution, evidence, exclusions, owners, or confirmation status
- Treating meeting notes as an approved scope
