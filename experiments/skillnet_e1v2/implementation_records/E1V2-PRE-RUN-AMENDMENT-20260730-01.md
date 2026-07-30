# E1-v2 PRE-RUN AMENDMENT

## Control

- Amendment ID: `E1V2-PRE-RUN-AMENDMENT-20260730-01`
- Scope: formal-run identity evidence, per-task process evidence, verifier
  isolation checks, and one condition-level analysis count
- Explicit exclusions: no Gold, task, GoldRelevantSkills, candidate-pool,
  Catalogue, relation, semantic-normalization, per-task metric-semantic,
  protected E0/E1, or formal-result change
- Formal model tasks started: `0`

## Changes

- Replaced the impossible self-referential SHA rule with a two-layer freeze:
  an immutable `setup_content_commit` and one evidence-only direct child
  `freeze_record_commit`.
- Formal execution now uses one serial `subprocess.Popen` per task and records
  the child PID, event-derived thread ID, temporary CWD, timing, redacted
  command, exit status, and single-attempt policy.
- The verifier checks process evidence, unique thread IDs and temporary CWDs,
  `--ephemeral`, absence of resume/continue, and fixture null evidence.
- Added `skill_routing_true_control_false` as a non-gating condition analysis
  count without changing any per-task success semantics.

## Verification

- E1-v2 tests: 29 passed
- Old evaluator: 16 passed, 2 environment-dependent skips
- Old experiment artifact tests: 6 passed
- Repository suite: 146 passed
- Deterministic Setup/Candidate/Catalogue validation: passed; 21 tasks and 189
  Catalogues
- Gold validation: passed; temporary output matched the frozen validation
- Fixture dry run: 21/21 passed with valid fixture process evidence and zero
  formal model tasks
- Existing non-benchmark synthetic smoke evidence: hashes and validity
  revalidated; no new model process started
- Runtime unchanged: Codex CLI `0.146.0-alpha.3.1`, model `gpt-5.6-sol`,
  reasoning `high`, Python `3.9.6`, jsonschema `4.25.1`
- Semantic normalization SHA-256 unchanged:
  `1b78b64b4a36cda5ec3a7146d4ce2a1aa910881fefe182bf1790103f3d49fc3c`

## Freeze

- Official setup content commit:
  `dbef338be1612e000b89d1c21f5deb8e5e6b214b`
- Final artifact hash bundle:
  `a7c15a3ab537218c2d51419e74f86a7b4010266ad8aa77d4c90762ab306cb46c`
- Freeze record commit: this record and final Setup evidence will be committed
  together as the direct child of the setup content commit
- Rollback: human-authorized Git revert of the evidence commit followed by the
  content commit; no data or formal-result rollback is required
