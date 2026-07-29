---
name: technology-specification-confirmation
description: Use when a feasible technology requirement needs confirmed performance, interface, compatibility, security, acceptance, and procurement technical parameters; not for architecture design or implementation.
---

# Technology Specification Confirmation

## Overview

Freeze measurable technical obligations before architecture design or technical procurement. This stage defines what must be satisfied, not how the solution is built.

**中文摘要：** 确认性能、接口、兼容性、安全、验收指标和采购技术参数；不负责架构、组件、部署或回滚方案。

## Required Inputs

- Approved requirement and feasibility IDs/versions, chosen option, constraints, and evidence
- Current interface contracts, environment/platform versions, data classification, security/privacy policy, and compatibility matrix
- Measurable performance/reliability targets, acceptance methods, procurement category needs, owners, and reviewers

## Workflow

1. Read `assets/technology_specification_template.md`; assign `specification_id` and version.
2. Trace each proposed specification to an approved requirement or feasibility constraint.
3. Confirm measurable performance, capacity, availability, reliability, recovery, and operability thresholds.
4. Confirm interface inputs/outputs, protocol/schema/version, error behavior, authentication, and compatibility obligations.
5. Confirm security, privacy, data-handling, audit, regulatory, and support constraints without claiming certification.
6. Define acceptance metrics, test methods, environments, tolerances, evidence, and owners.
7. Produce supplier-neutral technical procurement parameters where purchasing is involved.
8. Route baseline, deviations, and unresolved trade-offs to authorized owners.

## Output Contract

Return specification/requirement/feasibility IDs and versions, performance/interface/compatibility/security requirements, acceptance matrix, procurement parameters, assumptions, evidence, deviations, reviewers, and `status: human_review_required`.

## SkillNet Relationships

- Part of `technology-agent`.
- Enhances `procurement-rfq-generation` when `technical_specification_available`.
- Follows `technology-feasibility-assessment`.
- Precedes `procurement-requirement` when `external_technology_procurement`.
- Precedes `technology-solution-design`.

## Approval Controls

- Use stable IDs, minimum necessary metadata, restricted artifact references, source dates, owners, and append-only version/audit evidence.
- Do not invent benchmarks, interface guarantees, compatibility, certifications, security clearance, acceptance, or procurement approval.
- Human approval is required for the baseline, deviations, security/privacy acceptance, procurement parameters, and material threshold changes.

## Exception Handling

- Block design handoff when targets are unmeasurable, interface versions conflict, compatibility evidence is missing, or acceptance methods cannot demonstrate the requirement.
- Record unresolved constraints and named decision owners rather than selecting an architecture to hide ambiguity.

## Handoff

Pass the approved specification version, traceability matrix, fixed constraints, acceptance measures, evidence gaps, and human decision record to `technology-solution-design`; pass only approved procurement parameters to `procurement-rfq-generation`.

## Example

Confirm latency, availability, API schema, supported browsers, encryption, audit events, acceptance tests, and supplier-neutral hosting parameters for onboarding.

## Common Mistakes

- Choosing components or deployment topology in the specification
- Using vague terms such as “fast” or “secure”
- Claiming compatibility or acceptance without evidence
