---
name: hr-job-requirement
description: Use when a manager requests headcount, proposes opening a role, or needs a hiring request clarified and approved; not for writing or publishing the JD.
---

# HR Job Requirement

## Overview

Turn an informal hiring request into an approval-ready role brief. Establish the business need, outcomes, constraints, and decision owners before drafting a JD.

**中文摘要：** 收集并分析岗位需求，形成可审批的岗位需求说明书。

## Required Inputs

- Requesting manager and department
- Business problem and expected outcomes
- Headcount type, location, start date, and urgency
- Budget range and reporting line
- Required capabilities and measurable success indicators
- Replacement or new-headcount status

## Workflow

1. Confirm the business problem and why existing capacity cannot address it.
2. Classify the request as new headcount, replacement, internship, contractor, or temporary support.
3. Define role outcomes for the first 6–12 months before listing credentials.
4. Separate essential capabilities from trainable or preferred capabilities.
5. Record budget, level, location, employment type, reporting line, interviewer, and target start date.
6. Check for overlapping open roles and alternatives such as internal transfer or contractor support.
7. List missing decisions and route the complete brief through the company’s headcount approval chain.

## Output Contract

Return:

- `request_id`, `department`, and `hiring_manager`
- `business_need` and `role_outcomes`
- `headcount_type`, `employment_type`, `level`, and `location`
- `essential_capabilities` and `preferred_capabilities`
- `budget_range`, `target_start_date`, and `interview_owner`
- `alternatives_considered`, `missing_information`, and `approval_route`

## SkillNet Relationships

- Entry node for the recruiting path.
- Precedes `hr-jd-generator`.
- Conflicts with publishing or screening when headcount approval is absent.
- May query `hr-employee-database` for internal skills coverage using minimum necessary data.

## Approval Controls

- Do not encode protected characteristics or discriminatory preferences.
- Do not invent budget, level, or approval status.
- Human approval is required before opening headcount.

## Exception Handling

- Return requests with missing business need, owner, budget, level, location, outcomes, employment type, or approval route.
- Escalate overlapping roles, discriminatory criteria, or unresolved internal-transfer alternatives rather than opening recruitment.

## Handoff

Pass the approved request ID/version, role outcomes, essential/preferred capabilities, budget, constraints, interview owner, and approval evidence to `hr-jd-generator`; keep unapproved drafts closed.

## Example

“We need an AI product manager” becomes a brief with business outcome, first-year deliverables, essential skills, level, budget, reporting line, start date, alternatives, and approval route.

## Common Mistakes

- Copying credentials from a competitor’s JD without defining outcomes
- Treating every manager preference as mandatory
- Starting recruitment without budget or headcount approval
- Using demographic proxies such as age, gender, or family status
