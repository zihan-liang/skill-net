---
name: technology-test-acceptance
description: Use when a system version or implementation needs test evidence aggregation, quality-gate checks, defect review, environment-specific acceptance, or release-readiness input.
---

# Technology Test Acceptance

## Overview

Evaluate reproducible test evidence and blocking defects without converting automated gates into a human acceptance decision.

**中文摘要：** 汇总并复核测试套件、通过率、覆盖率、缺陷和证据，形成测试验收建议；自动门禁通过不等于人工验收或生产发布批准。

## Required Inputs

- Requirement/design/implementation IDs, `system_id`, `version_id`, environment, and acceptance criteria
- Required test suites, exact commands, runtime/configuration, timestamps, counts, and evidence references
- Coverage/pass thresholds and source, defect IDs/severity/status/evidence, and residual risks
- Tester, technical/product/security approvers, exception policy, and release dependency

## Workflow

1. Verify the version/artifact and environment exactly match the evidence under review.
2. Map every acceptance criterion and required suite to a reproducible result.
3. Run `scripts/evaluate_test_acceptance.py` to recompute counts, pass rate, coverage gates, suite completeness, and blocking defects.
4. Review unit, integration, contract, end-to-end, performance, security, migration, recovery, and operational tests as applicable.
5. Separate failed, skipped, flaky, not-run, environment-limited, and accepted-risk results.
6. Reproduce material failures or stale evidence; record retest links and superseded runs.
7. Summarize residual risk, defect disposition, evidence gaps, and rollback/recovery validation.
8. Route technical, product, security, and business acceptance to named authorized humans.

## Output Contract

Return test/system/version IDs, environment, suites/criteria/evidence, recomputed totals/pass rate, coverage, defects, blocking findings, residual risks, automated gate result, approvers, and evidence-based `acceptance_status`.

## SkillNet Relationships

- Follows `technology-development-implementation` and precedes `technology-system-release`.
- Supplies test evidence to operations and future maintenance/regression work.
- Persists confirmed test records through `technology-database`.

## Guardrails

- Do not invent commands, results, coverage, defect status, environments, exceptions, or approval evidence.
- Do not reuse development/staging evidence as production validation without explicit relevance.
- Human approval is required for acceptance, risk exceptions, defect deferral, and release readiness.

## Example

Evaluate onboarding version 1.4 staging evidence, recompute 98/100 passed, confirm 85% coverage, flag two skipped tests, and route final acceptance.

## Common Mistakes

- Counting missing or skipped suites as passed
- Trusting reported totals without reconciliation
- Ignoring environment, artifact version, flaky tests, or open high defects
- Treating an automated green gate as release approval
