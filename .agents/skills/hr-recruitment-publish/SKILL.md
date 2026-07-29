---
name: hr-recruitment-publish
description: Use when an approved JD needs channel adaptation, publication preflight, tracking fields, or confirmed publication recording; not for changing role criteria or screening applicants.
---

# HR Recruitment Publish

## Overview

Prepare a controlled multi-channel recruitment package from one approved JD. Keep role facts consistent while adapting format, call to action, and tracking fields.

**中文摘要：** 将已审批JD适配到招聘平台、内推和社交渠道，并生成渠道跟踪表。

## Required Inputs

- Approved canonical JD and request ID
- Target candidate profile and hiring location
- Approved channels, budget, dates, and owner
- Application URL or contact method
- Company brand and privacy wording

## Workflow

1. Confirm the JD is approved and record its version.
2. Select channels based on role seniority, location, specialization, urgency, and budget.
3. Adapt the approved JD to each channel’s length and formatting without changing selection criteria.
4. Create employee-referral and social-post copy with the same application route.
5. Add channel, campaign, source, owner, publication date, expiry date, cost, and tracking-code fields.
6. Check links, dates, contact details, compensation wording, and privacy notice.
7. Present the publication package for confirmation; record actual publication status only after confirmation.

## Output Contract

Return:

- `source_request_id` and `jd_version`
- `channel_plan` with rationale, owner, budget, and dates
- `platform_posts`
- `employee_referral_copy`
- `social_copy`
- `tracking_table`
- `preflight_checks`
- `publication_status`

## SkillNet Relationships

- Blocked by `finance-budget-check` when `recruitment_budget_not_approved`.
- Part of `hr-agent`.
- Follows `hr-jd-generator`.
- Precedes `hr-resume-screening`.

## Approval Controls

- Conflicts with external publication when headcount, JD, channel, or budget approval is missing.
- Do not publish, message candidates, or spend channel budget without explicit authority.
- Do not change approved qualifications across channels.
- Human confirmation is required before every external publication action.

## Exception Handling

- Block publication for stale JD versions, broken application routes, inconsistent criteria, missing privacy wording, expired dates, or unapproved channel spend.
- Record actual platform status only from evidence; preserve corrections as versioned posts.

## Handoff

Pass the request/JD versions, confirmed channel/post IDs, publication evidence, source codes, expiry dates, and applicant intake route to `hr-resume-screening`; do not invent applications.

## Example

For an approved AI engineer JD, produce a full recruitment-platform post, concise referral copy, two social variants, and tracking rows sharing one request ID and application link.

## Common Mistakes

- Publishing an outdated JD version
- Using different essential criteria on different platforms
- Omitting source tracking or expiry dates
- Claiming a role is published when only copy was prepared
