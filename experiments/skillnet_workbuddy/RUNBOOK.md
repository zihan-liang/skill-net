# SkillNet E0/E1 WorkBuddy Adapter — RUNBOOK

This directory contains the WorkBuddy/CodeBuddy-specific transport adapter
for SkillNet E0/E1 C-group (graph-structured) experiments. It mirrors the
frozen contract of `experiments/skillnet/` but uses `codebuddy`/`cbc` CLI
instead of `codex`.

## Scope

Only C-group (graph-structured) conditions:

- E0-C: size 46, GT01–GT21
- E1-C: size 10, 5 Gold tasks
- E1-C: size 30, 5 Gold tasks
- E1-C: size 46 (reuse E0-C)

A/B condition requests MUST be rejected.

## Transport requirement

The adapter requires a **non-interactive CodeBuddy CLI binary** (`codebuddy`
or `cbc`) installed on the local machine, with the following capabilities:

The following flags were confirmed against the installed binary
(`codebuddy --help`, v2.115.0), not from documentation guesses:

| Capability | Flag (verified on v2.115.0) |
|------------|------|
| Non-interactive one-shot execution | `-p` / `--print` |
| Exact model specification | `--model <MODEL_ID>` |
| Per-task new UUID session | `--session-id <uuid>` |
| Disable all built-in tools | `--tools ""` |
| Disable MCP | `--strict-mcp-config` (no `--mcp-config` passed) |
| Disable fallback | omit `--fallback-model` (fallback is opt-in only) |
| Memory isolation | `--system-prompt-file <file>` (overrides default system prompt) |
| Single agentic turn | `--max-turns 1` |
| Mechanical stdout/stderr capture | `--output-format text` + standard pipes |
| Exit code signalling | Non-zero on failure |

On Windows the installed CLI is an extensionless Node.js script which
CreateProcess cannot execute directly (WinError 193). The adapter
therefore invokes it via `cli_invocation()`, which prefixes a Node
runtime (`$CODEBUDDY_NODE`, then PATH, then the managed runtime under
`~/.workbuddy/binaries/node/versions/`). The full argv (prefix included)
is recorded in `condition_metadata.json` (`cli_invocation`) and per-task
`run_metadata.json` (`command`), together with the real child PID.

If the CLI binary is missing or any required capability is absent, the
adapter MUST report `WORKBUDDY_TRANSPORT_NOT_FORMAL_READY` and stop.

## Isolation contract

Every task starts a new `codebuddy exec` (or equivalent) process in a fresh
temporary working directory. The child receives only:

1. The current Chinese task (one of the 21 or 5 Gold tasks)
2. The one C-group Catalogue for the current condition
3. Fixed eight-field JSON output contract

The child is explicitly forbidden from using tools or reading files. It never
receives Gold, evaluator, `.agents/skills/`, relations, other Catalogues,
other tasks, or prior results.

## Output paths

```
runs/<MODEL_SLUG>/<experiment>/<configuration>/size_<size>/<run_id>/
results/<MODEL_SLUG>/<experiment>/<configuration>/size_<size>/<run_id>/
```

`<MODEL_SLUG>` isolates runs by model. The directory structure mirrors the
Codex adapter but is fully separated under `experiments/skillnet_workbuddy/`.

## Artifacts per task

Same contract as `experiments/skillnet/RUNBOOK.md`:

1. `run_metadata.json`
2. `packet_manifest.json`
3. `catalogue_snapshot.json`
4. `codebuddy_events.jsonl` (CLI stdout bytes)
5. `raw_response.txt`
6. `prediction.json` (only on valid schema)
7. `schema_validation.json`
8. `evaluation_trace.json`
9. `graph_overlay.json`
10. `result_row.json`

## Verification

Uses the same deterministic evaluator at:
`SkillNet_Gold_Tasks_V4/evaluation/evaluate_skillnet.py`

E1 frozen gold at:
`experiments/skillnet/frozen_eval/E1_Gold_5_tasks.json`

## Formal preflight

Before each condition:

1. `git rev-parse HEAD` == `git rev-parse origin/main`
2. Working tree clean
3. Catalogue validation and E1 gold validation pass
4. CLI binary, version, model, and capabilities confirmed
5. MODEL_ID confirmed via synthetic smoke
6. No drift in frozen inputs

## Transport readiness

If this RUNBOOK is reached without a valid `codebuddy`/`cbc` binary, the
adapter has already reported `WORKBUDDY_TRANSPORT_NOT_FORMAL_READY` and all
formal operations are blocked.
