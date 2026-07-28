---
name: hr-jd-generator
description: Use when an approved role brief must become a canonical, bilingual, or channel-adaptable job description; not for approving headcount or publishing the role.
---

# HR JD Generator

## Overview

Create an accurate, inclusive, outcome-oriented job description from an approved role brief. Preserve the approved scope while adapting length and tone for each channel.

**中文摘要：** 根据已审批的岗位需求生成适配不同招聘渠道的职位描述。

## Required Inputs

- Approved role brief from `hr-job-requirement`
- Company and team introduction
- Employment type, location, level, and compensation disclosure policy
- Application process and contact channel
- Target platform and language

## Workflow

1. Read `assets/jd_template.md` and map every approved field into it.
2. Lead with the role mission and measurable outcomes, then list responsibilities.
3. Separate essential capabilities from preferred capabilities; remove credentials that do not predict performance.
4. State location, working arrangement, employment type, application process, and compensation only as approved.
5. Review wording for gender, age, nationality, family-status, disability, and elite-school proxies.
6. Produce a canonical JD plus requested channel variants without changing the requirements.
7. Mark missing approved facts rather than inventing them.

## Output Contract

Return:

- `canonical_jd`
- `channel_variants` keyed by platform
- `language_versions`
- `source_request_id`
- `missing_information`
- `bias_review_notes`
- `publication_status: draft`

## SkillNet Relationships

- Requires an approved `hr-job-requirement` output.
- Precedes `hr-recruitment-publish`.
- Conflicts with publication when mandatory facts or headcount approval are missing.

## Approval Controls

- Do not add requirements, compensation, benefits, or promises absent from the approved brief.
- Do not use protected characteristics or proxies as selection criteria.
- Human confirmation is required before any JD is published externally.

## Exception Handling

- Mark missing approved facts and return scope, compensation, location, or criteria conflicts to the role owner.
- Remove discriminatory or unsupported requirements without inventing replacements; escalate material scope changes for a new role-brief version.

## Handoff

Pass the approved canonical JD/version, channel variants, application route, missing facts, bias review, and publication authority to `hr-recruitment-publish`; do not mark it published.

## Example

Convert an approved AI product manager brief into a complete canonical JD, a concise referral post, and a platform-length variant while keeping the same essential criteria.

## Common Mistakes

- Writing a company advertisement instead of explaining role outcomes
- Combining essential and preferred requirements
- Inflating years-of-experience requirements without evidence
- Letting channel adaptation change the approved role scope
