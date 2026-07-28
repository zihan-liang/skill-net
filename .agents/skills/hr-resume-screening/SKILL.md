---
name: hr-resume-screening
description: Use when resumes or candidate profiles need evidence-based screening against approved role criteria and a shortlist review packet; not for scheduling interviews or deciding final selection.
---

# HR Resume Screening

## Overview

Create a transparent five-dimension assessment from job-related evidence. Treat missing evidence as unknown, keep scores auditable, and reserve advancement decisions for humans.

**中文摘要：** 按五个岗位相关维度筛选简历，输出证据、评分、排名与信息缺口。

## Required Inputs

- Approved role criteria and dimension weights
- Candidate ID and resume evidence
- Evidence source or resume location for each claim
- Screening owner and review deadline

## Workflow

1. Remove or exclude protected and non-job-related candidate information.
2. Map resume evidence to five dimensions: essential capabilities, relevant experience, evidence of impact, domain context, and learning/collaboration.
3. Cite evidence verbatim or by source location; mark absent evidence as missing rather than inferring it.
4. Encode the scorecard as JSON and run `scripts/screen_resume.py`.
5. Review evidence coverage before comparing weighted scores.
6. Produce a shortlist recommendation, manual-review queue, and draft rejection rationale based only on approved criteria.
7. Require an authorized reviewer to decide advancement or rejection.

## Output Contract

Return:

- `candidate_id`
- five `dimensions` with score, weight, evidence, and contribution
- `weighted_score` and `evidence_coverage`
- `missing_dimensions`
- `recommendation_band`
- `decision_status: human_review_required`

## SkillNet Relationships

- Requires an approved role from `hr-job-requirement` and applications from `hr-recruitment-publish`.
- Precedes `hr-interview-scheduling`.
- Conflicts with demographic, photo, family-status, or other protected-characteristic scoring.

## Approval Controls

- Do not infer protected characteristics or treat missing evidence as a negative fact.
- Do not send rejection messages automatically.
- Human approval is required for shortlist, rejection, and ranking use.

## Exception Handling

- Exclude protected or unrelated data and route unreadable, incomplete, conflicting, or low-evidence profiles to manual review.
- Keep missing evidence unknown rather than scoring it negatively; preserve reviewer changes with evidence.

## Handoff

Pass only human-shortlisted candidate IDs, job-related evidence, scorecards, gaps, accommodations route, and decision evidence to `hr-interview-scheduling`; keep notices as drafts.

## Example

Map an AI product candidate’s shipped agents, activation impact, consumer-app work, and cross-functional launch to the five dimensions, then calculate the transparent scorecard.

## Common Mistakes

- Keyword matching without evidence context
- Comparing totals with materially different evidence coverage
- Treating school prestige, age, photo, or career gaps as performance evidence
- Presenting a recommendation band as a final decision
