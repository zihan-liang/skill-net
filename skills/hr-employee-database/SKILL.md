---
name: hr-employee-database
description: Use when authorized HR users need to query employees, update skills, record KPI or training information, manage personnel statistics, or audit employee-record changes.
---

# HR Employee Database

## Overview

Maintain a privacy-minimized, auditable employee record across onboarding, skills, KPI, and training workflows. Use stable employee IDs and record every mutation.

**中文摘要：** 管理员工基本信息、技能、KPI和培训记录，并为每次数据变更保留审计日志。

## Required Inputs

- Authorized actor and stated business purpose
- Employee ID and validated mutation or query fields
- Data owner approval for sensitive or consequential changes
- Database path and applicable retention/access policy

## Workflow

1. Read `references/employee_schema.md` and select only the tables and fields required for the purpose.
2. Confirm authorization, employee identity, data source, and whether the action is a query or mutation.
3. For local demos, initialize SQLite with `scripts/employee_db.py --database PATH init`.
4. Present every proposed mutation for confirmation, including before/after values and actor.
5. Run the relevant upsert only after confirmation; require evidence for skill and KPI changes.
6. Query by employee ID and minimize returned fields in the final response.
7. Verify the audit record and report the result without exposing unrelated personal data.

## Output Contract

Return:

- `operation`, `business_purpose`, and `authorized_actor`
- `employee_id`
- `fields_read` or `before_after_change`
- `evidence_reference`
- `audit_event_id` and timestamp for mutations
- `access_or_retention_notes`

## SkillNet Relationships

- Receives confirmed hiring data from `hr-onboarding`.
- May provide internal skills coverage to `hr-job-requirement` using aggregated, minimized data.
- Enhances onboarding, training, KPI, and workforce-planning workflows.

## Guardrails

- Do not store protected, medical, family, or unrelated personal data in general employee fields.
- Do not perform silent mutations, broad data dumps, or unaudited corrections.
- Human confirmation is required before every employee-record mutation.

## Example

After manager confirmation, update employee E-002’s Python proficiency with a production-service evidence reference, then return the changed fields and audit event rather than the full employee record.

## Common Mistakes

- Using names as primary identifiers
- Mixing candidate and employee records before acceptance
- Returning full profiles for a narrow query
- Updating skills or KPIs without evidence and actor attribution
