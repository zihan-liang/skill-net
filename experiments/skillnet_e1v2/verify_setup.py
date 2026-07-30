#!/usr/bin/env python3
"""Freeze E1-v2 Setup hashes and verify protected E0/E1 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
E1V2_DIR = Path(__file__).resolve().parent
EVIDENCE_DIR = E1V2_DIR / "setup_evidence"
PROTECTED_ROOTS = [
    ".agents/skills",
    "skillnet_run_guide_v1_1/catalogues",
    "skillnet_run_guide_v1_1/scale_relations",
    "experiments/skillnet/runs",
    "experiments/skillnet/results",
    "SkillNet_Gold_Tasks_V4/predictions",
    "SkillNet_Gold_Tasks_V4/results",
]
PROTECTED_FILES = [
    "SkillNet_Gold_Tasks_V4/02_Gold_Standard_21_V4.json",
    "experiments/skillnet/frozen_eval/E1_Gold_5_tasks.json",
    "experiments/skillnet/frozen_eval/E1_Gold_5_tasks_validation.json",
    "skill_relations.json",
    "SkillNet_Gold_Tasks_V4/evaluation/prediction_schema.json",
    "SkillNet_Gold_Tasks_V4/evaluation/evaluate_skillnet.py",
    "experiments/skillnet/run_condition.py",
    "experiments/skillnet/verify_condition.py",
]
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
FREEZE_RECORD_ALLOWED_PREFIXES = (
    "experiments/skillnet_e1v2/setup_evidence/",
    "experiments/skillnet_e1v2/implementation_records/",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def protected_snapshot(label: str) -> dict[str, Any]:
    files = []
    for relative in PROTECTED_ROOTS:
        base = ROOT / relative
        if base.exists():
            files.extend(path for path in base.rglob("*") if path.is_file())
    for relative in PROTECTED_FILES:
        path = ROOT / relative
        if path.is_file():
            files.append(path)
    unique = sorted(
        set(files), key=lambda path: path.relative_to(ROOT).as_posix()
    )
    records = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in unique
    ]
    bundle = sha256_bytes(
        "".join(
            f"{record['path']}\0{record['sha256']}\n"
            for record in records
        ).encode("utf-8")
    )
    return {
        "schema_version": "1.0",
        "snapshot": label,
        "hash_algorithm": "SHA-256",
        "file_count": len(records),
        "bundle_sha256": bundle,
        "files": records,
    }


def subset_snapshot(
    snapshot: dict[str, Any], token: str
) -> dict[str, Any]:
    files = [
        record for record in snapshot["files"] if token in record["path"]
    ]
    bundle = sha256_bytes(
        "".join(
            f"{record['path']}\0{record['sha256']}\n"
            for record in files
        ).encode("utf-8")
    )
    return {
        "path_token": token,
        "file_count": len(files),
        "bundle_sha256": bundle,
    }


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def assess_freeze_identity(
    *,
    local_head: str,
    origin_head: str,
    direct_parent: str,
    official_setup_content_commit: str,
    changed_paths: list[str],
    working_tree_clean: bool,
) -> dict[str, Any]:
    """Evaluate the non-self-referential two-layer freeze contract."""
    disallowed_paths = sorted(
        path
        for path in changed_paths
        if not any(
            path.startswith(prefix)
            for prefix in FREEZE_RECORD_ALLOWED_PREFIXES
        )
    )
    checks = {
        "local_head_equals_origin_main": local_head == origin_head,
        "working_tree_clean": working_tree_clean,
        "head_direct_parent_equals_official_setup_content_commit": (
            direct_parent == official_setup_content_commit
        ),
        "freeze_record_diff_only_contains_allowed_evidence": (
            not disallowed_paths
        ),
        "head_is_not_setup_content_commit": (
            local_head != official_setup_content_commit
        ),
    }
    return {
        "schema_version": "E1V2-1.0",
        "protocol": "two_layer_non_self_referential_freeze",
        "local_head": local_head,
        "origin_main": origin_head,
        "head_direct_parent": direct_parent,
        "official_setup_content_commit_sha": (
            official_setup_content_commit
        ),
        "changed_paths_from_setup_content_to_head": sorted(changed_paths),
        "allowed_freeze_record_prefixes": list(
            FREEZE_RECORD_ALLOWED_PREFIXES
        ),
        "disallowed_paths": disallowed_paths,
        "checks": checks,
        "valid": all(checks.values()),
    }


def git_output(repo: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return process.stdout.strip()


def check_freeze_identity(
    repo: Path,
    official_setup_content_commit: str,
) -> dict[str, Any]:
    local_head = git_output(repo, "rev-parse", "HEAD")
    origin_head = git_output(repo, "rev-parse", "origin/main")
    direct_parent = git_output(repo, "rev-parse", "HEAD^")
    changed_paths = [
        line
        for line in git_output(
            repo,
            "diff",
            "--name-only",
            f"{official_setup_content_commit}..HEAD",
        ).splitlines()
        if line
    ]
    working_tree_clean = not git_output(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    return assess_freeze_identity(
        local_head=local_head,
        origin_head=origin_head,
        direct_parent=direct_parent,
        official_setup_content_commit=official_setup_content_commit,
        changed_paths=changed_paths,
        working_tree_clean=working_tree_clean,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--protected-before",
        type=Path,
        default=Path("/tmp/skillnet_e1v2_protected_before.json"),
    )
    parser.add_argument(
        "--official-setup-content-commit",
        help=(
            "Full SHA-1 of the setup_content_commit. When omitted, preserve "
            "the value already recorded in the freeze manifest."
        ),
    )
    parser.add_argument(
        "--check-freeze-identity",
        action="store_true",
        help=(
            "Read-only formal preflight check of HEAD, origin/main, direct "
            "parent, clean tree, and the allowed freeze-record diff."
        ),
    )
    args = parser.parse_args()
    freeze_manifest_path = EVIDENCE_DIR / "setup_freeze_manifest.json"
    previous_freeze_manifest = (
        load(freeze_manifest_path)
        if freeze_manifest_path.is_file()
        else {}
    )
    official_setup_content_commit = (
        args.official_setup_content_commit
        or previous_freeze_manifest.get(
            "official_setup_content_commit_sha"
        )
    )
    if official_setup_content_commit and not COMMIT_SHA.fullmatch(
        official_setup_content_commit
    ):
        raise SystemExit(
            "--official-setup-content-commit must be a full lowercase "
            "40-character SHA-1"
        )
    if args.check_freeze_identity:
        if not official_setup_content_commit:
            raise SystemExit(
                "Freeze manifest has no official_setup_content_commit_sha"
            )
        identity = check_freeze_identity(
            ROOT,
            official_setup_content_commit,
        )
        print(json.dumps(identity, ensure_ascii=False, indent=2))
        return 0 if identity["valid"] else 3
    if not args.protected_before.is_file():
        raise SystemExit(f"Missing before snapshot: {args.protected_before}")
    before = load(args.protected_before)
    after = protected_snapshot("after")
    before_by_path = {item["path"]: item for item in before["files"]}
    after_by_path = {item["path"]: item for item in after["files"]}
    added = sorted(set(after_by_path) - set(before_by_path))
    removed = sorted(set(before_by_path) - set(after_by_path))
    changed = sorted(
        path
        for path in set(before_by_path) & set(after_by_path)
        if before_by_path[path] != after_by_path[path]
    )
    identical = not added and not removed and not changed
    before_copy = dict(before)
    before_copy["snapshot"] = "before"
    write_json(EVIDENCE_DIR / "protected_hashes_before.json", before_copy)
    write_json(EVIDENCE_DIR / "protected_hashes_after.json", after)
    comparison = {
        "schema_version": "E1V2-1.0",
        "experiment_id": "E1V2",
        "identical": identical,
        "before_file_count": before["file_count"],
        "after_file_count": after["file_count"],
        "before_bundle_sha256": before["bundle_sha256"],
        "after_bundle_sha256": after["bundle_sha256"],
        "added_protected_files": added,
        "removed_protected_files": removed,
        "changed_protected_files": changed,
        "run_02_before": subset_snapshot(before, "/run_02/"),
        "run_02_after": subset_snapshot(after, "/run_02/"),
    }
    comparison["run_02_identical"] = (
        comparison["run_02_before"] == comparison["run_02_after"]
    )
    write_json(EVIDENCE_DIR / "protected_hash_comparison.json", comparison)

    catalogue_root = (
        ROOT / "skillnet_run_guide_v1_1" / "e1v2_catalogues"
    )
    artifact_paths = {
        "gold": (
            ROOT
            / "SkillNet_Gold_Tasks_V4"
            / "e1v2"
            / "E1V2_Gold_21.json"
        ),
        "gold_relevant_skills": (
            ROOT
            / "SkillNet_Gold_Tasks_V4"
            / "e1v2"
            / "gold_relevant_skills.json"
        ),
        "gold_validation": (
            ROOT
            / "SkillNet_Gold_Tasks_V4"
            / "e1v2"
            / "E1V2_Gold_validation.json"
        ),
        "candidate_pool_manifest": (
            catalogue_root / "candidate_pool_manifest.json"
        ),
        "catalogue_manifest": catalogue_root / "catalogue_manifest.json",
        "candidate_pool_validation": (
            catalogue_root / "candidate_pool_validation_report.json"
        ),
        "catalogue_validation": (
            catalogue_root / "catalogue_validation_report.json"
        ),
        "semantic_normalization": (
            E1V2_DIR / "semantic_normalization.json"
        ),
        "metric_definitions": E1V2_DIR / "metric_definitions.json",
        "evaluator": E1V2_DIR / "evaluate_e1v2.py",
        "prediction_schema_wrapper": (
            E1V2_DIR / "prediction_schema_e1v2.json"
        ),
        "runner": E1V2_DIR / "run_condition.py",
        "verifier": E1V2_DIR / "verify_condition.py",
        "builder": E1V2_DIR / "build_setup.py",
        "setup_verifier": E1V2_DIR / "verify_setup.py",
        "synthetic_smoke": E1V2_DIR / "synthetic_smoke.py",
        "fixture_dry_run": E1V2_DIR / "fixture_dry_run.py",
        "runbook": E1V2_DIR / "RUNBOOK.md",
        "fixture_dry_run_evidence": (
            EVIDENCE_DIR / "fixture_dry_run_setup_01.json"
        ),
        "fixture_dry_run_amendment_evidence": (
            EVIDENCE_DIR
            / "fixture_dry_run_pre_run_amendment_01.json"
        ),
        "synthetic_smoke_validation": (
            EVIDENCE_DIR
            / "synthetic_smoke"
            / "setup_01"
            / "validation.json"
        ),
        "synthetic_smoke_raw_response": (
            EVIDENCE_DIR
            / "synthetic_smoke"
            / "setup_01"
            / "raw_response.txt"
        ),
        "test_commands": EVIDENCE_DIR / "test_commands.json",
        "protected_hash_comparison": (
            EVIDENCE_DIR / "protected_hash_comparison.json"
        ),
    }
    missing = [
        name for name, path in artifact_paths.items() if not path.is_file()
    ]
    hashes = {
        name: {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
        }
        for name, path in artifact_paths.items()
        if path.is_file()
    }
    candidate_validation = (
        load(artifact_paths["candidate_pool_validation"])
        if artifact_paths["candidate_pool_validation"].is_file()
        else {"valid": False}
    )
    catalogue_validation = (
        load(artifact_paths["catalogue_validation"])
        if artifact_paths["catalogue_validation"].is_file()
        else {"valid": False}
    )
    gold_validation = (
        load(artifact_paths["gold_validation"])
        if artifact_paths["gold_validation"].is_file()
        else {"valid": False}
    )
    fixture_validation = (
        load(artifact_paths["fixture_dry_run_evidence"])
        if artifact_paths["fixture_dry_run_evidence"].is_file()
        else {"valid": False}
    )
    fixture_amendment_validation = (
        load(artifact_paths["fixture_dry_run_amendment_evidence"])
        if artifact_paths["fixture_dry_run_amendment_evidence"].is_file()
        else {"valid": False}
    )
    synthetic_validation = (
        load(artifact_paths["synthetic_smoke_validation"])
        if artifact_paths["synthetic_smoke_validation"].is_file()
        else {"valid": False}
    )
    artifact_hash_bundle = sha256_bytes(
        "".join(
            f"{name}\0{record['path']}\0{record['sha256']}\n"
            for name, record in sorted(hashes.items())
        ).encode("utf-8")
    )
    formal_roots = [
        E1V2_DIR / "runs" / "E1V2",
        E1V2_DIR / "results" / "E1V2",
    ]
    formal_artifacts = [
        path
        for formal_root in formal_roots
        if formal_root.exists()
        for path in formal_root.rglob("*")
        if path.is_file()
    ]
    e1v2_run_01_paths = [
        path
        for formal_root in formal_roots
        if formal_root.exists()
        for path in formal_root.rglob("*")
        if "e1v2_run_01" in path.parts
    ]
    ready = all(
        [
            identical,
            comparison["run_02_identical"],
            not missing,
            gold_validation.get("valid") is True,
            candidate_validation.get("valid") is True,
            catalogue_validation.get("valid") is True,
            fixture_validation.get("valid") is True,
            fixture_amendment_validation.get("valid") is True,
            synthetic_validation.get("valid") is True,
            fixture_validation.get("formal_model_tasks_started") == 0,
            fixture_amendment_validation.get(
                "formal_model_tasks_started"
            )
            == 0,
            synthetic_validation.get("formal_model_task") is False,
            not formal_artifacts,
            not e1v2_run_01_paths,
        ]
    )
    freeze_manifest = {
        "schema_version": "E1V2-1.0",
        "experiment_id": "E1V2",
        "setup_status": "READY" if ready else "STOPPED",
        "freeze_record_status": (
            "official"
            if official_setup_content_commit
            else "provisional"
        ),
        "freeze_protocol": {
            "name": "two_layer_non_self_referential_freeze",
            "setup_content_commit": (
                "contains final runner, verifier, metrics, tests, and "
                "experiment content"
            ),
            "freeze_record_commit": (
                "direct child containing only setup_evidence and "
                "implementation_records changes"
            ),
            "head_must_equal_setup_content_commit": False,
            "head_direct_parent_must_equal_setup_content_commit": True,
            "allowed_freeze_record_prefixes": list(
                FREEZE_RECORD_ALLOWED_PREFIXES
            ),
        },
        "official_setup_content_commit_sha": (
            official_setup_content_commit
        ),
        "artifact_hashes": hashes,
        "artifact_hash_bundle_sha256": artifact_hash_bundle,
        "semantic_normalization_sha256": hashes.get(
            "semantic_normalization", {}
        ).get("sha256"),
        "metric_definitions_sha256": hashes.get(
            "metric_definitions", {}
        ).get("sha256"),
        "protected_files_identical": identical,
        "run_02_identical": comparison["run_02_identical"],
        "candidate_pool_validation": candidate_validation,
        "catalogue_validation": catalogue_validation,
        "gold_validation_passed": gold_validation.get("valid") is True,
        "fixture_dry_run_passed": fixture_validation.get("valid") is True,
        "fixture_dry_run_amendment_passed": (
            fixture_amendment_validation.get("valid") is True
        ),
        "synthetic_smoke_passed": synthetic_validation.get("valid") is True,
        "formal_model_tasks_started": len(formal_artifacts),
        "e1v2_run_01_path_count": len(e1v2_run_01_paths),
        "missing_artifacts": missing,
    }
    write_json(freeze_manifest_path, freeze_manifest)
    print(json.dumps(freeze_manifest, ensure_ascii=False, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
