# SkillNet E4 A/B/C Fuzzy-Language Experiment Summary

**Experiment:** E4 fuzzy-language robustness

**Catalogue size:** 46 atomic skills

**Tasks:** GT01–GT21 (21 tasks per configuration)

**Selected runs:** A/B/C `run_02`

**Runtime repository commit:** `1861e51f6f0142c98bf4cd5d5b7fa4b7842876cd`

**Report date:** 2026-07-31

> **Interpretation boundary:** This report describes one formal run per configuration. It does not establish statistical significance or causal superiority. E4 changes the user prompt from explicit process language to short, natural Chinese while preserving each task's initial state, goal, stopping boundary, required and forbidden skills, ordering constraints, final status, blockers, and route choice.

## Executive summary

All three E4 configurations completed as formal single-batch runs. Each configuration produced 21 raw responses, 21 schema-valid predictions, no invalid predictions, a complete artifact contract, and evaluator exit code 0.

Configurations A and C tied for the highest functional and clean success at **10/21 (47.62%)**; B achieved **9/21 (42.86%)**. The tie masks a substantial difference in routing quality. C, the graph-structured catalogue, recorded the strongest Skill F1 (**89.13%**), department F1 (**100%**), required-order accuracy (**98.10%**), and lowest constraint-violation rate (**42.86%**). A retained perfect no-tool accuracy but had markedly lower Skill recall and order accuracy. B generally fell between A and C on routing metrics, while losing one no-tool task.

The E0-to-E4 comparison is mixed. A's functional success was unchanged, B improved by two tasks, and C declined by two tasks. B's apparent improvement must be interpreted cautiously because its formal E0 baseline contained four model-produced format-invalid outputs, whereas E4-B produced valid JSON for all 21 tasks. Across the more route-sensitive metrics, fuzzy language reduced Skill F1 for all three configurations and sharply reduced A's required-order accuracy. C was the most robust representation on Skill selection and ordering, but it did not preserve overall functional success because GT12 and GT20 regressed.

Every configuration solved all six simple tasks (GT01–GT06), and none solved any of the three special-constraint tasks (GT16–GT18). Route-choice accuracy was identical at **76.19%**, and blocked-flow accuracy remained **0%** for A, B, and C. The principal unresolved weakness is therefore constraint execution—especially blocking, alternative-route selection, and mutual exclusion—rather than basic department identification.

## Formal-run and artifact status

| Configuration | Catalogue representation | Selected run | Raw responses | Valid predictions | Invalid predictions | Artifact contract | Evaluator exit | Formal status |
|---|---|---:|---:|---:|---:|---|---:|---|
| A | Flat catalogue | `run_02` | 21 | 21 | 0 | complete | 0 | Formal single batch |
| B | Department-grouped catalogue | `run_02` | 21 | 21 | 0 | complete | 0 | Formal single batch |
| C | Graph-structured catalogue | `run_02` | 21 | 21 | 0 | complete | 0 | Formal single batch |

Each selected run contains 212 run-artifact files and 55 verification/evaluator-result files. Across A/B/C, the publication bundle contains **801 evidence files and 6,248,781 bytes** before this report. All 63 child processes used one fresh attempt, exited with code 0, saved a raw response and prediction, used the frozen runtime commit, and ran with a read-only child sandbox.

## E4 overall metrics

| Metric | A | B | C | Best observed |
|---|---:|---:|---:|---|
| Functional success | **47.62% (10/21)** | 42.86% (9/21) | **47.62% (10/21)** | A/C tie |
| Clean success | **47.62%** | 42.86% | **47.62%** | A/C tie |
| Skill precision | 89.16% | 88.92% | **89.56%** | C |
| Skill recall | 89.03% | 93.65% | **98.41%** | C |
| Skill F1 | 83.36% | 86.14% | **89.13%** | C |
| Department precision | 100% | 100% | 100% | Tie |
| Department recall | 94.44% | 96.03% | **100%** | C |
| Department F1 | 96.51% | 97.46% | **100%** | C |
| Required-order accuracy | 81.69% | 88.48% | **98.10%** | C |
| Final-status accuracy | **80.95%** | 76.19% | **80.95%** | A/C tie |
| Route-choice accuracy | 76.19% | 76.19% | 76.19% | Tie |
| No-tool accuracy | **100%** | 66.67% | 66.67% | A |
| Blocked-flow accuracy | 0% | 0% | 0% | Tie |
| Gold-constraint violation rate | 47.62% | 47.62% | **42.86%** | C (lower is better) |

C's advantage is strongest on the structural metrics: compared with A, C improved Skill F1 by **5.77 percentage points**, department F1 by **3.49 points**, and required-order accuracy by **16.41 points**. This did not translate into higher overall success because functional success also requires correct final status, route choice, blocking behavior, and no-tool formatting.

## E0-to-E4 robustness

The fixed baselines are A `E0/A/size_46/run_02`, B `E0/B/size_46/run_02`, and C `E0/C/size_46/run_04`. The failed E0-C `run_02` and B's patched non-formal result are explicitly excluded.

| Configuration | E0 functional | E4 functional | Change | E0 Skill F1 | E4 Skill F1 | E0 order | E4 order | E0 constraints | E4 constraints |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 47.62% | 47.62% | 0.00pp | 88.48% | 83.36% | 93.01% | 81.69% | 42.86% | 47.62% |
| B | 33.33% | 42.86% | +9.52pp | 88.29% | 86.14% | 87.88% | 88.48% | 42.86% | 47.62% |
| C | 57.14% | 47.62% | -9.52pp | 89.58% | 89.13% | 99.05% | 98.10% | 38.10% | 42.86% |

| Configuration | E0 final status | E4 final status | E0 no-tool | E4 no-tool | E0 route choice | E4 route choice | E0 blocked flow | E4 blocked flow |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 76.19% | 80.95% | 100% | 100% | 76.19% | 76.19% | 0% | 0% |
| B | 47.62% | 76.19% | 0% | 66.67% | 76.19% | 76.19% | 0% | 0% |
| C | 85.71% | 80.95% | 100% | 66.67% | 76.19% | 76.19% | 0% | 0% |

The strongest robustness result is C's near-preservation of Skill F1 and ordering under fuzzy language. The weakest is A's order drop of **11.32 points**. B's functional and final-status gains are partly entangled with the disappearance of the four format-invalid E0-B outputs, so they should not be read as evidence that fuzzy wording made routing easier.

## Results by task category

| Category | Tasks | A successes | B successes | C successes |
|---|---:|---:|---:|---:|
| Single skill | 1 | 1/1 | 1/1 | 1/1 |
| Single-department goal | 5 | 5/5 | 5/5 | 5/5 |
| Cross-department goal | 9 | 1/9 | 1/9 | **2/9** |
| Special constraint | 3 | 0/3 | 0/3 | 0/3 |
| No tool | 3 | **3/3** | 2/3 | 2/3 |

C's additional cross-department success offsets its no-tool regression, producing the same total success count as A. Department grouping alone did not improve the number of successful cross-department tasks, although B's path-level recall and order accuracy were higher than A's.

## E4 task-level outcome matrix

`PASS` means evaluator `functional_success = true`. All listed failures came from schema-valid predictions.

| Task | Category | A | B | C |
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
| GT12 | Cross-department | FAIL | FAIL | FAIL |
| GT13 | Cross-department | FAIL | FAIL | FAIL |
| GT14 | Cross-department | PASS | PASS | PASS |
| GT15 | Cross-department | FAIL | FAIL | **PASS** |
| GT16 | Special constraint | FAIL | FAIL | FAIL |
| GT17 | Special constraint | FAIL | FAIL | FAIL |
| GT18 | Special constraint | FAIL | FAIL | FAIL |
| GT19 | No tool | PASS | PASS | PASS |
| GT20 | No tool | PASS | FAIL | FAIL |
| GT21 | No tool | PASS | PASS | PASS |

The results are highly stable at the task level. GT01–GT06, GT14, GT19, and GT21 succeeded in every configuration. GT07–GT13 and GT16–GT18 failed in every configuration. Catalogue representation changed only GT15 and GT20: C uniquely solved GT15, while A uniquely satisfied the strict no-tool output requirements for GT20.

## Failure-tag comparison

| Failure tag | A | B | C |
|---|---:|---:|---:|
| `CONFLICT_VIOLATION` | 2 | 2 | **1** |
| `CONTINUE_AFTER_BLOCK` | 2 | 2 | **1** |
| `FORBIDDEN_SKILL_VIOLATION` | 2 | 2 | **1** |
| `MISSING_DEPARTMENT` | 3 | 2 | **0** |
| `MISSING_REQUIRED_SKILL` | 7 | 5 | **2** |
| `MUTEX_VIOLATION` | **1** | **1** | 3 |
| `ORDER_VIOLATION` | 8 | 6 | **2** |
| `REPEATED_COMPLETED_SKILL` | 4 | 4 | 4 |
| `UNNECESSARY_SKILL` | 4 | 4 | 4 |
| `WRONG_BLOCK_REASON` | 1 | **0** | 1 |
| `WRONG_FINAL_STATUS` | 4 | 5 | 4 |
| `WRONG_ROUTE_CHOICE` | 5 | 5 | 5 |

C substantially reduced missing-Skill, missing-department, and order failures. Its main structural regression was mutual exclusion, with three violations versus one in A and B. None of the representations changed wrong-route-choice, repeated-completed-Skill, or unnecessary-Skill counts.

## Interpretation

1. **C best preserves atomic routes under fuzzy language.** Its high Skill recall, department coverage, and order accuracy show that embedded graph relations help recover long paths when intermediate steps are not named.
2. **Path recovery and functional success are distinct.** C reconstructed routes most accurately but only tied A on success because the evaluator also requires correct status, route choice, blocking, and strict no-tool behavior.
3. **Department grouping provides partial structure, not reliable routing.** B improved path recall and ordering over A, but it did not increase cross-department success and had the lowest total success count.
4. **Simple tasks are insensitive to catalogue representation.** All configurations solved every single-skill and single-department task, suggesting the main experiment signal lies in cross-department and constrained tasks.
5. **Constraint handling is the dominant unresolved problem.** All configurations failed GT16–GT18 and recorded 0% blocked-flow accuracy. Adding graph structure reduced some relation errors but did not teach the model to stop correctly.
6. **E4 produces a measurable robustness cost.** Relative to E0, all configurations lost Skill F1, and A/C lost order or functional performance. The exact magnitude requires replicated runs before inferential claims are appropriate.

## GT20 evaluator diagnostic note

For GT20 in B and C, the model correctly returned `use_skills: false`, empty departments, an empty Skill sequence, `final_status: "no_tool"`, and no blockers, but also returned a non-empty descriptive `route_choice` object. The frozen evaluator defines no-tool correctness as requiring `route_choice` to be empty, so both predictions are official functional failures.

The evaluator's general route-choice check passes vacuously when the Gold expected object is empty, and no dedicated failure tag is emitted for this case. Consequently, GT20 is recorded as a failure with no failure tag. This is a diagnostic coverage gap, not a missing artifact. No prediction or score was manually changed; the official metrics above retain the frozen evaluator result.

## Provenance and runtime

| Item | A | B | C |
|---|---|---|---|
| Catalogue SHA-256 | `2b0ad47bd9cf8d21932db3c4589f944f8fbed877de470d3e6659529b78f51d0e` | `077237c0ced54c4f51b7bd252838af7e282b70e1b8dd7207be1ab31f34adfc4c` | `d5854e08107adfc8b396eeb29f2ed0dd9392da1b93d0c369ffd9b3a5714835ef` |
| Runtime repository commit | `1861e51f6f0142c98bf4cd5d5b7fa4b7842876cd` | same | same |
| Gold SHA-256 | `62f711e21ecbc7703c6c6fddf71f871525337c972e00688a29c46a611e93748b` | same | same |
| Prediction schema SHA-256 | `fa1c552f341f86ed50db40a707cf40da6b0e1ccee83cda4fd1ca9505fe6ee1ce` | same | same |
| E4 Prompt manifest SHA-256 | `634ac0cb4a77d7d26ba9818c7a74395cbcec6c356691e6253cd6f9ad347cc293` | same | same |
| E4 semantic audit SHA-256 | `b404b82d3eb835cd271fb2d2f54520d42137ba8bdc7046602eb5b34d0501fa3b` | same | same |
| Common Prompt-set SHA-256 | `453fb088ef1a563263b15e2a090b99fcbf39cdbb1e1fde7fa6f08d301a20bc5b` | same | same |

The shared runtime was Codex CLI `0.146.0-alpha.3.1`, model `gpt-5.6-sol`, reasoning effort `high`, Python `3.9.6`, and `jsonschema 4.25.1`. Each task used a fresh ephemeral `codex exec` child with user configuration and repository rules ignored, read-only sandboxing, JSON events, one attempt, and no automatic retry.

## Audit bundles

- A run artifacts: [`../runs/E4/A/size_46/run_02`](../runs/E4/A/size_46/run_02)
- A verification/evaluator results: [`../results/E4/A/size_46/run_02`](../results/E4/A/size_46/run_02)
- B run artifacts: [`../runs/E4/B/size_46/run_02`](../runs/E4/B/size_46/run_02)
- B verification/evaluator results: [`../results/E4/B/size_46/run_02`](../results/E4/B/size_46/run_02)
- C run artifacts: [`../runs/E4/C/size_46/run_02`](../runs/E4/C/size_46/run_02)
- C verification/evaluator results: [`../results/E4/C/size_46/run_02`](../results/E4/C/size_46/run_02)

Each run directory contains condition metadata plus per-task catalogue snapshots, Codex events, raw responses, predictions, schema validation, evaluation traces, graph overlays, result rows, and runtime metadata. Each result directory contains the independently extracted predictions, verification records and manifest, evaluator invocation, per-task results, category/configuration summaries, failure analysis, and E0 robustness comparison.

## Verification commands

Run from the repository root:

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E4 --configuration A --size 46 --run-id run_02

experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E4 --configuration B --size 46 --run-id run_02

experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E4 --configuration C --size 46 --run-id run_02
```

The saved evidence for each verification is available in its result directory through `VERIFY_COMMAND.txt`, `verification_manifest.json`, `verification_records/`, `evaluator_invocation.json`, and `e0_robustness_comparison.json`. Existing formal artifacts are immutable; these commands are provenance records rather than instructions to overwrite them.

## Limitations and documented deviations

- One run per configuration is insufficient for confidence intervals, significance testing, or stable estimates of stochastic variance.
- E0-B's four format-invalid outputs make its E0-to-E4 functional improvement less directly comparable with A and C.
- All configurations failed the three special-constraint tasks and recorded 0% blocked-flow accuracy.
- Route-choice accuracy remained 76.19% for every configuration.
- C reduced missing and ordering errors but retained three mutual-exclusion violations.
- GT20 exposes a frozen evaluator diagnostic gap: strict no-tool failure can occur without a failure tag when `route_choice` is non-empty.
- The outer orchestration environment could not explicitly request `sandbox_permissions=require_escalated`; it was already unrestricted, while every experimental child remained read-only.
- Transport reconnects, HTTP fallback, and state-database warnings occurred during the runs, but all 63 original child processes completed with exit code 0 and no replacement attempt.
- During E4-C, two unrelated untracked E0 Markdown files appeared in the shared checkout. They were not referenced by any C child event, all C children ran in unique temporary directories, and tracked inputs remained unchanged. These files are excluded from this publication commit.
- Synthetic smoke evidence was stored outside the formal run/result trees and is not part of this publication bundle.

No raw response, prediction, trace, overlay, result row, or evaluator output in the selected E4 runs was manually repaired or replaced.
