#!/usr/bin/env python3
"""Run and preserve a fixture-only E1-v2 runner/verifier Setup summary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


E1V2_DIR = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-id", required=True)
    args = parser.parse_args()
    evidence_path = (
        E1V2_DIR
        / "setup_evidence"
        / f"fixture_dry_run_{args.evidence_id}.json"
    )
    if evidence_path.exists():
        raise SystemExit(f"Evidence exists: {evidence_path}")
    with tempfile.TemporaryDirectory(
        prefix="skillnet_e1v2_fixture_"
    ) as temporary:
        state_root = Path(temporary) / "state"
        run_id = f"fixture_{args.evidence_id}"
        runner_command = [
            sys.executable,
            str(E1V2_DIR / "run_condition.py"),
            "--configuration",
            "A",
            "--size",
            "10",
            "--run-id",
            run_id,
            "--fixture-response-dir",
            str(E1V2_DIR / "fixtures" / "gold_perfect"),
            "--state-root",
            str(state_root),
        ]
        runner_process = subprocess.run(
            runner_command,
            text=True,
            capture_output=True,
            check=False,
        )
        verifier_command = [
            sys.executable,
            str(E1V2_DIR / "verify_condition.py"),
            "--configuration",
            "A",
            "--size",
            "10",
            "--run-id",
            run_id,
            "--state-root",
            str(state_root),
        ]
        verifier_process = subprocess.run(
            verifier_command,
            text=True,
            capture_output=True,
            check=False,
        )
        result_root = (
            state_root
            / "results"
            / "E1V2"
            / "A"
            / "size_10"
            / run_id
        )
        run_root = (
            state_root
            / "runs"
            / "E1V2"
            / "A"
            / "size_10"
            / run_id
        )
        summary_path = result_root / "condition_summary.json"
        validation_path = run_root / "condition_validation.json"
        summary = (
            json.loads(summary_path.read_text(encoding="utf-8"))
            if summary_path.is_file()
            else None
        )
        validation = (
            json.loads(validation_path.read_text(encoding="utf-8"))
            if validation_path.is_file()
            else None
        )
        valid = bool(
            runner_process.returncode == 0
            and verifier_process.returncode == 0
            and validation
            and validation.get("status") == "complete"
            and summary
            and summary.get("strict_functional_success") == 1.0
            and summary.get("semantic_functional_success") == 1.0
            and summary.get("skill_routing_success") == 1.0
            and summary.get("control_success") == 1.0
            and summary.get("consistency_counts", {}).get(
                "semantic_true_skill_routing_false"
            )
            == 0
        )
        evidence = {
            "schema_version": "E1V2-1.0",
            "experiment_id": "E1V2",
            "evidence_id": args.evidence_id,
            "execution_mode": "fixture",
            "formal_model_tasks_started": 0,
            "temporary_state_deleted_after_validation": True,
            "runner": {
                "command": runner_command,
                "exit_code": runner_process.returncode,
                "stdout": runner_process.stdout,
                "stderr": runner_process.stderr,
            },
            "verifier": {
                "command": verifier_command,
                "exit_code": verifier_process.returncode,
                "stdout": verifier_process.stdout,
                "stderr": verifier_process.stderr,
            },
            "condition_validation": validation,
            "condition_summary": summary,
            "valid": valid,
        }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
