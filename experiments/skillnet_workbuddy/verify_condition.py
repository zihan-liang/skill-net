#!/usr/bin/env python3
"""Thin verifier wrapper for the WorkBuddy SkillNet C-group adapter.

This does NOT reimplement scoring. It invokes the FROZEN verifier
``experiments/skillnet/verify_condition.py`` against this adapter's per-model
state-root, so the frozen evaluator and the frozen evaluation_trace /
graph_overlay / result_row writing are reused verbatim (zero scoring drift).

Only C-group conditions are forwarded. Any A/B request is rejected here before
the frozen verifier is reached.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import run_condition as rc


def repository_root() -> Path:
    return rc.repository_root()


def frozen_verifier_path(repo: Path) -> Path:
    return repo / "experiments" / "skillnet" / "verify_condition.py"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--experiment", choices=("E0", "E1"), required=True)
    p.add_argument("--configuration", choices=("C",), required=True)
    p.add_argument("--size", type=int, required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--model-slug", default="", help="MODEL_SLUG (per-model state-root)")
    p.add_argument("--state-root", type=Path, default=None, help=argparse.SUPPRESS)
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if args.configuration not in rc.ALLOWED_CONFIGURATIONS:
        raise SystemExit(f"Only C configuration allowed; got {args.configuration}")
    if (args.experiment, args.size) not in rc.ALLOWED_CONDITIONS:
        raise SystemExit(
            "Only E0-C-size46, E1-C-size10, E1-C-size30, E1-C-size46 allowed; "
            f"got {args.experiment}-C-size{args.size}"
        )
    if not rc.RUN_ID_PATTERN.fullmatch(args.run_id):
        raise SystemExit("run_id must match [A-Za-z0-9][A-Za-z0-9._-]*")

    repo = repository_root()
    if args.state_root is not None:
        state_root = args.state_root.resolve()
    else:
        if not args.model_slug or not rc.MODEL_SLUG_PATTERN.fullmatch(args.model_slug):
            raise SystemExit(
                "--model-slug (lowercase letters/digits/underscore) is required "
                "when --state-root is not given"
            )
        state_root = rc.default_state_root(args.model_slug)

    frozen_verify = frozen_verifier_path(repo)
    if not frozen_verify.is_file():
        raise SystemExit(f"Frozen verifier not found: {frozen_verify}")

    # Forward to the frozen verifier with this adapter's per-model state-root.
    # The frozen verifier reads runs from <state_root>/runs/... and writes
    # results to <state_root>/results/..., reusing the frozen evaluator.
    command = [
        sys.executable, str(frozen_verify),
        "--experiment", args.experiment,
        "--configuration", args.configuration,
        "--size", str(args.size),
        "--run-id", args.run_id,
        "--state-root", str(state_root),
    ]
    proc = subprocess.run(command, cwd=str(repo), text=True, capture_output=True, check=False)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
