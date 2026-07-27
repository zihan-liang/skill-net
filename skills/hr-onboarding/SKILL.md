---
name: hr-onboarding
description: Use when a candidate accepts an offer, a new employee needs onboarding, a manager needs a 30/60/90-day plan, or a probation review or confirmation is approaching.
---

# HR Onboarding

## Overview

Coordinate a secure, role-specific onboarding and probation process from accepted offer through confirmation. Make every task, owner, due date, and evidence requirement explicit.

**中文摘要：** 管理新员工入职清单、30/60/90天计划、试用期反馈与转正评估。

## Required Inputs

- Accepted offer and approved start date
- Employee identity data collected through an authorized channel
- Manager, buddy, department, location, and employment type
- Role outcomes and probation duration
- Required equipment, accounts, access, policies, and training

## Workflow

1. Verify offer acceptance and authoritative start information.
2. Read `assets/onboarding.md` and assign preboarding, first-day, first-week, and compliance tasks.
3. Apply least-privilege access: request only systems required for the role and name each approving owner.
4. Build 30/60/90-day outcomes from the approved role brief, not generic activity lists.
5. Schedule manager check-ins, training, feedback, and probation-review deadlines.
6. Track completion evidence, blockers, and overdue actions without exposing unnecessary personal data.
7. Prepare the probation summary and route confirmation, extension, or other employment decisions to authorized humans.
8. Update `hr-employee-database` only after confirmation of the record contents.

## Output Contract

Return:

- `employee_id`, `start_date`, `manager`, and `buddy`
- `onboarding_checklist` with owners and due dates
- `access_requests` and approval status
- `plan_30_60_90`
- `check_in_schedule` and `training_plan`
- `probation_evidence`, `blockers`, and `decision_status`

## SkillNet Relationships

- Requires an accepted and approved `hr-offer-generator` output.
- Contains preboarding, access, training, check-in, and probation-review tasks.
- Updates `hr-employee-database` after confirmed milestones.

## Guardrails

- Do not request sensitive identity documents through unapproved channels.
- Do not grant system access or make probation decisions automatically.
- Human approval is required for access, probation extension, confirmation, or termination.

## Example

For a new AI engineer, assign laptop and repository access, policy training, team introductions, first-release outcomes, check-ins, and probation evidence with named owners and dates.

## Common Mistakes

- Treating onboarding as paperwork rather than role enablement
- Granting broad access “just in case”
- Creating activity-based goals with no measurable outcome
- Missing statutory or company probation deadlines
