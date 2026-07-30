# SkillNet E0 A/B/C Experiment Summary

**Experiment:** E0

**Catalogue size:** 46 skills

**Tasks:** GT01–GT21 (21 tasks per configuration)

**Runtime repository commit:** `f392adc6bc2bdd6a64e8e6b29f943f68ece161a8`

**Report date:** 2026-07-30

> **Important provenance note:** A (`run_02`) and C (`run_04`) are formal single-batch runs. B is the explicitly labelled composite `run_02_PATCHED_NONFORMAL`: GT01–GT16 and GT21 came from the original B `run_02`, while GT17–GT20 came from a later user-authorized supplemental execution after transport failures. B has a complete, valid 21-task artifact set, but it is **not formal-eligible** and must be treated as descriptive evidence rather than a strict formal A/B/C comparison point.

## Executive summary

Configuration C (graph-structured catalogue) produced the strongest result in this set: **12/21 functional and clean successes (57.14%)**, compared with A at **10/21 (47.62%)** and patched B at **9/21 (42.86%)**. C's clearest advantage appeared on cross-department tasks, where it succeeded on 3/9 tasks versus 1/9 for A and B. It also had the highest required-order accuracy (99.05%), final-status accuracy (85.71%), department F1 (100%), and the lowest gold-constraint violation rate (38.10%).

The gain is not universal. All configurations solved every single-skill and single-department task, and none solved any of the three special-constraint tasks. Route-choice accuracy was identical at 76.19%. C reduced missing-skill, order, conflict, and final-status failures, but increased mutual-exclusion violations from 1 to 4. The experiment therefore supports C as the best observed catalogue representation for this run set, especially for cross-department sequencing, while leaving blocked-flow and special-constraint handling as the primary unresolved weakness.

Because there is only one selected run per configuration and B is a mixed-batch composite, these results are descriptive and do not establish statistical significance or causal superiority.

## Compared runs and audit status

| Configuration | Catalogue representation | Selected run | Raw responses | Valid predictions | Invalid predictions | Artifact contract | Evaluator exit | Formal status |
|---|---|---:|---:|---:|---:|---|---:|---|
| A | Flat catalogue | `run_02` | 21 | 21 | 0 | complete | 0 | Formal single batch |
| B | Department-grouped catalogue | `run_02_PATCHED_NONFORMAL` | 21 | 21 | 0 | complete | 0 | **Non-formal mixed batch** |
| C | Graph-structured catalogue | `run_04` | 21 | 21 | 0 | complete | 0 | Formal single batch |

Each selected run has a 21-task `condition_validation.json` matrix with `status: complete`, no missing or unexpected artifacts, and schema-valid predictions for all 21 tasks. Each corresponding `verification_manifest.json` records 21 raw responses, 21 valid predictions, zero invalid predictions, and evaluator exit code 0.

A direct read-only audit of the selected run directories also found 21 task directories per configuration, 21/21 child exit codes equal to 0, no missing required task artifacts, and no empty `raw_response.txt` or `codex_events.jsonl` files.

## Overall metrics

| Metric | A | B patched | C | Best observed |
|---|---:|---:|---:|---|
| Functional success | 47.62% (10/21) | 42.86% (9/21) | **57.14% (12/21)** | C |
| Clean success | 47.62% | 42.86% | **57.14%** | C |
| Skill precision | **90.14%** | 90.11% | 89.64% | A |
| Skill recall | 96.78% | 96.44% | **99.21%** | C |
| Skill F1 | 88.48% | 88.29% | **89.58%** | C |
| Department precision | 100% | 100% | 100% | Tie |
| Department recall | 96.83% | 96.83% | **100%** | C |
| Department F1 | 98.10% | 98.10% | **100%** | C |
| Required-order accuracy | 93.01% | 92.64% | **99.05%** | C |
| Final-status accuracy | 76.19% | 66.67% | **85.71%** | C |
| Route-choice accuracy | 76.19% | 76.19% | 76.19% | Tie |
| No-tool accuracy | 100% | 66.67% | 100% | A/C |
| Blocked-flow accuracy | 0% | 0% | 0% | Tie |
| Gold-constraint violation rate | 42.86% | 42.86% | **38.10%** | C (lower is better) |

C exceeded A by **9.52 percentage points** in functional success and B by **14.29 points**. Relative to A, C improved required-order accuracy by 6.04 points and final-status accuracy by 9.52 points. Relative to patched B, those improvements were 6.41 and 19.05 points, respectively.

## Results by task category

| Category | Tasks | A successes | B patched successes | C successes |
|---|---:|---:|---:|---:|
| Single skill | 1 | 1/1 | 1/1 | 1/1 |
| Single-department goal | 5 | 5/5 | 5/5 | 5/5 |
| Cross-department goal | 9 | 1/9 | 1/9 | **3/9** |
| Special constraint | 3 | 0/3 | 0/3 | 0/3 |
| No tool | 3 | 3/3 | 2/3 | 3/3 |

The catalogue representation made no measurable difference on the six simpler single-skill and single-department tasks: every configuration solved all of them. C's net advantage came from cross-department tasks GT12 and GT14, in addition to GT15, which all configurations solved. Patched B lost one no-tool success because GT21 was functionally incorrect despite having a valid prediction artifact.

## Task-level outcome matrix

`PASS` means evaluator `functional_success = true`; `FAIL` means a schema-valid prediction was evaluated but did not satisfy the functional criteria.

| Task | Category | A | B patched | C |
|---|---|---:|---:|---:|
| GT01 | Single skill | PASS | PASS | PASS |
| GT02 | Single-department | PASS | PASS | PASS |
| GT03 | Single-department | PASS | PASS | PASS |
| GT04 | Single-department | PASS | PASS | PASS |
| GT05 | Single-department | PASS | PASS | PASS |
| GT06 | Single-department | PASS | PASS | PASS |
| GT07 | Cross-department | FAIL | FAIL | FAIL |
| GT08 | Cross-department | FAIL | FAIL | FAIL |
| GT09 | Cross-department | FAIL | FAIL | FAIL |
| GT10 | Cross-department | FAIL | FAIL | FAIL |
| GT11 | Cross-department | FAIL | FAIL | FAIL |
| GT12 | Cross-department | FAIL | FAIL | **PASS** |
| GT13 | Cross-department | FAIL | FAIL | FAIL |
| GT14 | Cross-department | FAIL | FAIL | **PASS** |
| GT15 | Cross-department | PASS | PASS | PASS |
| GT16 | Special constraint | FAIL | FAIL | FAIL |
| GT17 | Special constraint | FAIL | FAIL | FAIL |
| GT18 | Special constraint | FAIL | FAIL | FAIL |
| GT19 | No tool | PASS | PASS | PASS |
| GT20 | No tool | PASS | PASS | PASS |
| GT21 | No tool | PASS | FAIL | PASS |

Common failures across all three configurations were GT07–GT11, GT13, and GT16–GT18. These tasks concentrate the remaining difficulty in multi-stage cross-department routing and special/blocked decision logic.

## Failure-tag comparison

| Failure tag | A | B patched | C |
|---|---:|---:|---:|
| `CONFLICT_VIOLATION` | 2 | 2 | **1** |
| `CONTINUE_AFTER_BLOCK` | 2 | 2 | **1** |
| `FORBIDDEN_SKILL_VIOLATION` | 2 | 2 | **1** |
| `MISSING_DEPARTMENT` | 2 | 2 | **0** |
| `MISSING_REQUIRED_SKILL` | 4 | 4 | **1** |
| `MUTEX_VIOLATION` | **1** | **1** | 4 |
| `ORDER_VIOLATION` | 4 | 4 | **1** |
| `REPEATED_COMPLETED_SKILL` | 3 | 3 | 3 |
| `UNNECESSARY_SKILL` | 3 | 3 | 3 |
| `WRONG_FINAL_STATUS` | 5 | 7 | **3** |
| `WRONG_ROUTE_CHOICE` | 5 | 5 | 5 |

C removed missing-department failures and substantially reduced missing-required-skill, ordering, and final-status errors. Its main regression was `MUTEX_VIOLATION`, which rose to four instances. `WRONG_ROUTE_CHOICE`, repeated-skill behavior, and unnecessary-skill behavior did not improve.

## Interpretation

1. **C is the strongest observed representation.** Its graph structure aligns with the experiment's hardest cross-department sequencing demands and yielded the best overall success rate.
2. **B did not improve on A in this evidence set.** Department grouping alone matched A on cross-department success and underperformed it on final status and one no-tool task. Because B is patched non-formal, this is an exploratory observation, not a formal negative result.
3. **The principal bottleneck is constraint execution, not basic skill discovery.** Skill and department recall are already high, while functional success remains much lower because ordering, blocking, route choice, mutual exclusion, and final status determine the outcome.
4. **Graph structure changes the error profile rather than eliminating constraint errors.** C improved ordering and completeness, but its higher mutual-exclusion error count suggests a need for clearer alternative-path semantics or stronger exclusivity cues.
5. **Special-constraint behavior requires separate attention.** Zero blocked-flow accuracy and 0/3 special-constraint success across A, B, and C indicate a systematic weakness independent of catalogue representation.

## Provenance and runtime

| Item | A | B patched | C |
|---|---|---|---|
| Catalogue SHA-256 | `2b0ad47bd9cf8d21932db3c4589f944f8fbed877de470d3e6659529b78f51d0e` | `077237c0ced54c4f51b7bd252838af7e282b70e1b8dd7207be1ab31f34adfc4c` | `d5854e08107adfc8b396eeb29f2ed0dd9392da1b93d0c369ffd9b3a5714835ef` |
| Catalogue source commit | `742e39d837484e5311e6663658bc7420c2a07a6b` | `742e39d837484e5311e6663658bc7420c2a07a6b` | `742e39d837484e5311e6663658bc7420c2a07a6b` |
| Runtime repository commit | `f392adc6bc2bdd6a64e8e6b29f943f68ece161a8` | same | same |
| Gold SHA-256 | `62f711e21ecbc7703c6c6fddf71f871525337c972e00688a29c46a611e93748b` | same | same |
| Prediction schema SHA-256 | `fa1c552f341f86ed50db40a707cf40da6b0e1ccee83cda4fd1ca9505fe6ee1ce` | same | same |

Shared runtime settings were Codex CLI `0.146.0-alpha.3.1`, model `gpt-5.6-sol`, reasoning effort `high`, Python `3.9.6`, and `jsonschema 4.25.1`. Each task used a fresh ephemeral `codex exec` child with read-only sandboxing, JSON events, one attempt, and no automatic retry. B's four supplemental task executions were separate later attempts and are fully identified in its `patch_provenance.json`.

## Audit bundles

The publication set includes the report plus these six directories. The three run directories contain per-task metadata, catalogue snapshots, raw responses, Codex JSONL events, predictions, schema validation, evaluation traces, graph overlays, and result rows. The three result directories contain independently extracted predictions, verification records/manifests, evaluator invocation records, per-task results, summaries, and failure analysis.

Together, the six selected audit directories contain 799 files and 6,205,692 bytes of evidence before adding this report. No individual file is larger than 56,821 bytes.

- A run artifacts: [`../runs/E0/A/size_46/run_02`](../runs/E0/A/size_46/run_02)
- A verification/evaluator results: [`../results/E0/A/size_46/run_02`](../results/E0/A/size_46/run_02)
- B patched run artifacts: [`../runs/E0/B/size_46/run_02_PATCHED_NONFORMAL`](../runs/E0/B/size_46/run_02_PATCHED_NONFORMAL)
- B patched verification/evaluator results: [`../results/E0/B/size_46/run_02_PATCHED_NONFORMAL`](../results/E0/B/size_46/run_02_PATCHED_NONFORMAL)
- C run artifacts: [`../runs/E0/C/size_46/run_04`](../runs/E0/C/size_46/run_04)
- C verification/evaluator results: [`../results/E0/C/size_46/run_04`](../results/E0/C/size_46/run_04)

The original failed B `run_02` and the standalone supplemental source directory are preserved locally but are outside this selected comparison publication bundle. Their task-level source mapping is retained inside the published composite B bundle in `patch_provenance.json`.

## Verification commands

Run from the repository root:

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E0 --configuration A --size 46 --run-id run_02

experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E0 --configuration B --size 46 --run-id run_02_PATCHED_NONFORMAL

experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E0 --configuration C --size 46 --run-id run_04
```

The saved evidence for each verification is available in its result directory through `VERIFY_COMMAND.txt`, `verification_manifest.json`, `verification_records/`, and `evaluator_invocation.json`.

## Limitations and remaining issues

- B is explicitly non-formal and mixed-batch; its results must not be presented as a protocol-compliant single-run control.
- One selected run per configuration is insufficient for confidence intervals, significance testing, or robust claims about variance.
- All configurations failed the three special-constraint tasks and recorded 0% blocked-flow accuracy.
- Route-choice accuracy remained 76.19% for all configurations.
- C's four mutual-exclusion violations are a material regression despite its higher overall success.
- The report compares evaluator outputs as recorded; no raw response, prediction, trace, or evaluator result was manually corrected.
