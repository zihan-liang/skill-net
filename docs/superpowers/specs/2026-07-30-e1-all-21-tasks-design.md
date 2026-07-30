# E1 All-21-Tasks Design

## Objective

Expand SkillNet E1 from the five-task scale subset to the complete canonical
GT01–GT21 task set while preserving the existing A/B/C Catalogue conditions,
model prompt contract, deterministic evaluator, and no-repair experiment
policy.

## Experiment semantics

E1 will answer a broader question than the original five-task design: how the
end-to-end performance of the same model changes when the visible Catalogue
contains 10, 30, or 46 Skills across flat, department-grouped, and
graph-structured representations.

For size 10 and size 30, every A/B/C condition runs all 21 canonical tasks.
Each task still starts one fresh Codex child process and receives only its
Chinese task and the selected condition Catalogue. The change therefore creates
six live conditions and 126 new model calls:

```text
2 live sizes × 3 configurations × 21 tasks = 126 calls
```

Size 46 remains a reuse condition. It starts no new model processes and uses
all 21 corresponding E0 outcomes for each configuration. The combined E1
analysis consequently contains 189 evaluated task outcomes: 126 new size-10
and size-30 outcomes plus 63 reused E0 size-46 outcomes.

The deterministic evaluator remains unchanged. If a size-10 or size-30
Catalogue does not expose a Skill required by a task, the resulting missing
Skill or unsuccessful route remains an ordinary evaluated failure. No task is
excluded, reweighted, repaired, or marked out of scope. This makes Catalogue
coverage part of the measured size effect.

## Canonical task inventory

`skillnet_run_guide_v1_1/E1_scale_manifest.json` remains the authoritative E1
task inventory and will explicitly list GT01 through GT21 in numeric order. The
runner and verifier must require that this list:

- contains exactly 21 unique IDs;
- equals the complete prompt inventory under
  `SkillNet_Gold_Tasks_V4/prompts/`;
- equals the complete canonical Gold task inventory; and
- stays in deterministic GT01–GT21 numeric order.

The existing `skill_sets` records for sizes 10 and 30 remain unchanged. They
describe the frozen Catalogue sizes, not task coverage. The manifest notes will
state that all tasks are deliberately evaluated even when the smaller
Catalogue omits required Skills.

## Frozen E1 Gold

The five-task frozen files will be retired:

- `experiments/skillnet/frozen_eval/E1_Gold_5_tasks.json`
- `experiments/skillnet/frozen_eval/E1_Gold_5_tasks_validation.json`

They will be replaced by:

- `experiments/skillnet/frozen_eval/E1_Gold_21_tasks.json`
- `experiments/skillnet/frozen_eval/E1_Gold_21_tasks_validation.json`

`verify_condition.py --prepare-e1-gold` will mechanically produce the new E1
Gold from the full canonical Gold and the 21-ID manifest. It must preserve every
task record at the JSON-value level, record the source Gold and manifest hashes,
set `task_count` to 21, and pass the existing Gold validator. E1 verification
will use this frozen 21-task file rather than silently falling back to another
Gold path.

## Runner and verifier behavior

For E1 size 10 and size 30, `run_condition.py` will resolve all 21 IDs from the
manifest and create the same per-task artifact contract already used by E0.
No prompt text, child CLI flags, isolation setting, model configuration, retry
policy, or artifact ownership rule changes.

`verify_condition.py` will expect the same 21 tasks, validate each immutable raw
response, and invoke the unchanged evaluator with the frozen E1 21-task Gold.
Invalid model JSON remains a formal model outcome when the child process itself
ran successfully; it is never patched or supplemented.

Formal E1 size-46 execution remains prohibited. Size-46 analysis must reference
the immutable E0 task outcomes instead of invoking `run_condition.py` for a new
model batch. The source mapping must retain its actual provenance rather than
renaming source run IDs:

| Configuration | Formal E0 source |
|---|---|
| A | `E0/A/size_46/run_02` |
| B | `E0/B/size_46/run_02` |
| C | `E0/C/size_46/run_04` |

The non-formal patched B bundle and the failed C run are excluded from the
formal E1 size-46 source set. Formal B `run_02` retains its model-produced
invalid responses as evaluated outcomes.

## Documentation and commands

The Setup Prompt, standard RUN commands, and RUNBOOK will consistently state:

- E1 uses GT01–GT21;
- size 10 and size 30 each run 21 tasks per A/B/C condition;
- size 46 reuses all 21 E0 tasks and starts no child processes;
- the six live conditions create 126 new model calls; and
- no five-task E1 restriction remains.

The existing condition command shape does not change. For example:

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py \
  --experiment E1 --configuration A --size 10 --run-id run_02 --execute
```

Each condition is still verified independently with
`verify_condition.py`. A/B/C and size conditions remain isolated in separate
parent conversations.

## Testing and validation

Regression tests will establish the new contract before production code is
changed. The test suite must verify:

1. the E1 manifest contains the complete ordered GT01–GT21 inventory;
2. runner condition resolution returns 21 tasks for E1 sizes 10, 30, and 46;
3. the frozen E1 Gold contains 21 JSON-value-identical canonical task records;
4. fixture runner and verifier flows create complete artifacts for all 21 tasks;
5. an invalid prediction remains absent while the other audit artifacts remain
   complete;
6. all renamed frozen-Gold paths exist and no active reference to the five-task
   filenames or five-task behavior remains;
7. all existing repository tests continue to pass; and
8. no real E0 or E1 model child is started during implementation validation.

The implementation will use fixture-only temporary directories for runner and
verifier tests. Existing E0 and failed/non-formal audit bundles remain immutable.

## Non-goals

This change does not:

- modify any Catalogue or Catalogue relation;
- add missing Skills to the size-10 or size-30 Catalogue;
- modify canonical Gold task content;
- modify the prediction schema or evaluator scoring rules;
- introduce coverage-aware filtering or alternative metrics;
- repair earlier E0 outputs;
- rerun E0 or E1 size 46; or
- start any formal experiment during implementation.

## Acceptance criteria

The change is complete when every code path, frozen artifact, test, and
instruction agrees that E1 contains exactly GT01–GT21; fixture verification
passes for 21 tasks; the repository suite is green; searches find no active
five-task E1 contract; and the formal command documentation reports 126 new
size-10/size-30 model calls with size 46 sourced from E0.
