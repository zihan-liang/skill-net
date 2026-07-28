# Employee Database Schema

Use this schema only for authorized HR operations. Query by employee ID and return the minimum fields needed for the stated purpose.

## `employees`

- `employee_id`: stable internal identifier; primary key
- `legal_name`: restricted identity field
- `preferred_name`: display name
- `department`, `job_title`, `manager_id`
- `employment_status`: controlled value such as `preboarding`, `active`, or `inactive`
- `start_date`, `work_email`
- `created_at`, `updated_at`: UTC audit timestamps

## `employee_skills`

One row per employee and skill. `proficiency` uses an evidence-backed 1–5 scale. Store a concise evidence reference rather than private source material.

## `kpi_records`

Store period, metric, target, actual, and status. Do not store unrelated manager commentary in KPI fields.

## `training_records`

Store course, completion status, completion date, and credential reference. Do not store medical or accommodation details.

## `audit_log`

Record actor, action, entity type, entity ID, before/after JSON, and UTC timestamp for every mutation. Audit records are append-only.

## Access Rules

- Require a stated business purpose and authorized role.
- Do not expose legal names, email addresses, KPI details, or training records in aggregate queries unless required.
- Separate candidate records from employee records until an offer is accepted.
- Apply retention, correction, export, and deletion rules from applicable company policy and law.
