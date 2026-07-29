---
name: hr-interview-scheduling
description: Use when shortlisted candidates need interview logistics, notices, interviewer assignment, structured scorecards, and feedback consolidation; not for resume screening or offer issuance.
---

# HR Interview Scheduling

## Overview

Coordinate a consistent interview process and collect job-related evidence across six dimensions. Separate logistics from evaluation and preserve independent interviewer feedback.

**中文摘要：** 安排面试、生成通知与六维评估表，并汇总形成可审计的面试决策材料。

## Required Inputs

- Approved role criteria and interview stages
- Candidate ID, contact channel, availability, and timezone
- Interviewer availability, role, and conflict declarations
- Meeting format, location or link, duration, and accommodations
- Decision owner and feedback deadline

## Workflow

1. Confirm candidate advancement from `hr-resume-screening` and the approved interview plan.
2. Resolve timezone, accessibility, confidentiality, and interviewer-conflict requirements.
3. Create a schedule with stage, objective, interviewer, duration, and backup owner.
4. Draft candidate and interviewer notices; do not send them without confirmation.
5. Read `assets/interview_eval.md` and tailor evidence prompts to the approved role criteria.
6. Collect independent scores before exposing other interviewers’ feedback.
7. Summarize evidence, disagreements, missing signals, and the authorized decision owner’s outcome.

## Output Contract

Return:

- `candidate_id`, `request_id`, and `interview_plan`
- `schedule` with timezone and owners
- `candidate_notice` and `interviewer_brief`
- `evaluation_forms`
- `feedback_summary`, `evidence_gaps`, and `decision_status`
- `communication_status: draft`

## SkillNet Relationships

- Blocks `hr-offer-generator` when `candidate_not_approved`.
- Part of `hr-agent`.
- Enhances `hr-employee-database` when `authorized_interview_evidence_available`.
- Follows `hr-resume-screening`.
- Precedes `hr-offer-generator`.

## Approval Controls

- Do not ask about protected characteristics, family plans, health history, or unrelated personal matters.
- Do not send invitations or rejection messages automatically.
- Human approval is required for advancement, rejection, and final selection.

## Exception Handling

- Reschedule or escalate timezone, accessibility, interviewer conflict, no-show, confidentiality, or missing-feedback issues without fabricating attendance.
- Preserve independent feedback and material disagreement; do not force consensus through averaging.

## Handoff

Pass only the authorized finalist decision, candidate/request IDs, evidence summary, conflicts, compensation prerequisites, and decision record to `hr-offer-generator`; do not imply an offer was made.

## Example

Create two interview stages for a product manager candidate, generate notices, assign interview objectives, and provide six-dimension scorecards with behavioral evidence prompts.

## Common Mistakes

- Scheduling without timezone confirmation
- Letting interviewers evaluate different criteria
- Averaging scores without explaining material disagreement
- Using vague “culture fit” judgments instead of job evidence
