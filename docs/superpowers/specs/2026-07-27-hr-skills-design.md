# HR Skills Design

## Goal

Create the eight independent Codex skills specified by the HR recruitment-flow diagram. Seven skills cover the recruiting lifecycle and one manages the employee database across the lifecycle.

## Packages

1. `hr-job-requirement`: collect and approve hiring requirements.
2. `hr-jd-generator`: create platform-ready job descriptions using `assets/jd_template.md`.
3. `hr-recruitment-publish`: prepare channel-specific posts, referral copy, and tracking data.
4. `hr-resume-screening`: score resumes across five dimensions using `scripts/screen_resume.py`.
5. `hr-interview-scheduling`: coordinate interviews and six-dimension evaluations using `assets/interview_eval.md`.
6. `hr-offer-generator`: validate compensation and generate offers using `scripts/generate_offer.py` and `assets/offer_template.md`.
7. `hr-onboarding`: manage onboarding and probation using `assets/onboarding.md`.
8. `hr-employee-database`: query and update employee records using `scripts/employee_db.py` and `references/employee_schema.md`.

## Common Skill Contract

Each package contains a `SKILL.md` with only `name` and trigger-oriented `description` frontmatter, concise imperative instructions, required inputs, workflow, output contract, SkillNet relations, privacy and human-approval guardrails, one example, and common mistakes. Each package also contains generated `agents/openai.yaml` metadata whose default prompt explicitly invokes the skill.

## Safety Boundaries

- Require approved headcount before publishing a role.
- Use job-related evidence only; do not infer or score protected characteristics.
- Keep rejection, advancement, compensation, offer, employment, and termination decisions under authorized human control.
- Minimize access to candidate and employee personal information.
- Require explicit confirmation before sending external messages, publishing a role, issuing an offer, or changing employee records.
- Preserve audit fields for scoring, interview decisions, offer approvals, and database mutations.

## Validation

Create a deterministic collection test before creating the packages. Test all Python resources before implementation and after completion. Run the official Codex `quick_validate.py` validator on each package and scan the repository for placeholders.
