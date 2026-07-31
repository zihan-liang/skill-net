#!/usr/bin/env python3
"""WorkBuddy/CodeBuddy transport adapter for SkillNet E0/E1 C-group conditions.

Scope: ONLY C-group (graph-structured) conditions are supported.
  - E0-C-size46   : GT01-GT21, real codebuddy child processes.
  - E1-C-size10   : 5 frozen Gold tasks, real codebuddy child processes.
  - E1-C-size30   : 5 frozen Gold tasks, real codebuddy child processes.
  - E1-C-size46   : DERIVED from the same model's E0-C-size46 run; no model call.
A/B condition requests are rejected.

Transport: the locally installed ``codebuddy`` CLI (never ``codex``). Each task
is a fresh, non-interactive ``codebuddy --print`` process with a new UUID
session, a fresh empty working directory, tools/MCP disabled, fallback omitted,
and the system prompt overridden to isolate memory injection. Transport stdout
is preserved byte-for-byte; structured results are extracted mechanically and
never repaired.

Verification is NOT performed here. After all responses exist, run
``verify_condition.py`` (a thin wrapper) which invokes the FROZEN
``experiments/skillnet/verify_condition.py`` against this adapter's per-model
state-root, reusing the frozen evaluator and scoring logic verbatim.

Run/output isolation:
  experiments/skillnet_workbuddy/<MODEL_SLUG>/runs/<exp>/<config>/size_<size>/<run_id>/
  experiments/skillnet_workbuddy/<MODEL_SLUG>/results/<exp>/<config>/size_<size>/<run_id>/
<MODEL_SLUG> is the per-model state-root so each model's runs/results are fully
isolated and the frozen verifier can be reused unchanged via --state-root.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


# ── Condition constants ────────────────────────────────────────────────

CONFIGURATION_FILENAMES = {
    "C": "C_graph_structured_catalogue.json",
}
ALLOWED_CONFIGURATIONS = {"C"}
# The only four formal conditions this adapter may run.
ALLOWED_CONDITIONS = {
    ("E0", 46),
    ("E1", 10),
    ("E1", 30),
    ("E1", 46),
}
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
MODEL_SLUG_PATTERN = re.compile(r"^[a-z0-9_]+$")
# Runner artifacts. NOTE: the events file is named ``codex_events.jsonl`` to
# match the frozen artifact inventory exactly, so the frozen verifier's
# required-artifact audit passes unchanged. Its content is the codebuddy
# transport stdout (see run_metadata.transport / events_source).
RUN_REQUIRED_ARTIFACTS = (
    "run_metadata.json",
    "packet_manifest.json",
    "catalogue_snapshot.json",
    "codex_events.jsonl",
    "raw_response.txt",
    "schema_validation.json",
)
TRANSPORT_NAME = "codebuddy"

# Known codebuddy install locations (checked after PATH and $CODEBUDDY_CLI).
KNOWN_CLI_PATHS = [
    Path("D:/AI-桌面助手/WorkBuddy/resources/app.asar.unpacked/cli/bin/codebuddy"),
    Path("/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/cli/bin/codebuddy"),
]


def resolve_node() -> Path | None:
    """Locate a Node.js runtime for executing JS CLI scripts on Windows."""
    env_node = os.environ.get("CODEBUDDY_NODE")
    if env_node and Path(env_node).is_file():
        return Path(env_node)
    found = shutil.which("node") or shutil.which("node.exe")
    if found:
        return Path(found)
    managed = Path.home() / ".workbuddy" / "binaries" / "node" / "versions"
    if managed.is_dir():
        for exe in sorted(managed.glob("*/node.exe"), reverse=True):
            if exe.is_file():
                return exe
    return None


def cli_invocation(cli: Path) -> list[str]:
    """Return the argv prefix used to execute the CLI.

    On Windows, CreateProcess cannot execute an extensionless Node.js
    script directly (WinError 193), so it must be prefixed with a Node
    runtime. Real executables (.exe/.bat/.cmd/.com) and non-Windows
    platforms (shebang) run directly.
    """
    if os.name == "nt" and cli.suffix.lower() not in {".exe", ".bat", ".cmd", ".com"}:
        node = resolve_node()
        if node is None:
            raise RuntimeError(
                "WORKBUDDY_TRANSPORT_NOT_FORMAL_READY: "
                "codebuddy CLI is a Node.js script but no node runtime was found "
                "(checked $CODEBUDDY_NODE, PATH, ~/.workbuddy managed runtimes)"
            )
        return [str(node), str(cli)]
    return [str(cli)]


# ── Generic helpers ────────────────────────────────────────────────────


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if exclusive:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
    else:
        path.write_text(data, encoding="utf-8")


def write_bytes(path: Path, data: bytes, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "xb" if exclusive else "wb"
    with path.open(mode) as handle:
        handle.write(data)


def git_head(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo, text=True, capture_output=True, check=True,
    )
    return proc.stdout.strip()


# ── Transport detection ────────────────────────────────────────────────


def locate_cli(explicit: Path | None = None) -> Path:
    """Resolve the codebuddy CLI binary. Never codex."""
    if explicit is not None:
        if not explicit.is_file():
            raise RuntimeError(
                "WORKBUDDY_TRANSPORT_NOT_FORMAL_READY: "
                f"explicit CLI path not a file: {explicit}"
            )
        return explicit
    env_path = os.environ.get("CODEBUDDY_CLI")
    if env_path:
        candidate = Path(env_path)
        if candidate.is_file():
            return candidate
    found = shutil.which("codebuddy") or shutil.which("cbc")
    if found:
        return Path(found)
    for candidate in KNOWN_CLI_PATHS:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "WORKBUDDY_TRANSPORT_NOT_FORMAL_READY: "
        "no codebuddy/cbc CLI found (checked PATH, $CODEBUDDY_CLI, known installs)"
    )


def cli_version(cli: Path) -> str:
    proc = subprocess.run(
        cli_invocation(cli) + ["--version"],
        text=True, capture_output=True, check=False,
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    return lines[0] if lines else "unknown"


def child_system_prompt_file() -> Path:
    return Path(__file__).resolve().parent / "child_system_prompt.txt"


# ── Prompt / catalogue helpers (mirror frozen contract exactly) ─────────


def extract_chinese_prompt(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    first = text.splitlines()[0] if text else ""
    if not first.startswith("Task ID: "):
        raise ValueError(f"Missing Task ID header: {path}")
    task_id = first.removeprefix("Task ID: ").strip()
    marker = "\n中文任务\n"
    end_marker = "\n\nOutput requirements"
    if marker not in text or end_marker not in text:
        raise ValueError(f"Cannot isolate Chinese prompt: {path}")
    prompt_zh = text.split(marker, 1)[1].split(end_marker, 1)[0].strip()
    if not prompt_zh:
        raise ValueError(f"Empty Chinese prompt: {path}")
    return task_id, prompt_zh


def load_prompt_map(repo: Path) -> dict[str, dict[str, str]]:
    prompt_dir = repo / "SkillNet_Gold_Tasks_V4" / "prompts"
    records: dict[str, dict[str, str]] = {}
    for path in sorted(prompt_dir.glob("GT*.txt")):
        task_id, prompt_zh = extract_chinese_prompt(path)
        if task_id in records:
            raise ValueError(f"Duplicate prompt task_id: {task_id}")
        records[task_id] = {
            "prompt_zh": prompt_zh,
            "source": str(path.relative_to(repo)),
            "sha256": sha256_file(path),
        }
    expected = list(range(1, 22))
    actual = sorted(int(tid[2:4]) for tid in records)
    if len(records) != 21 or actual != expected:
        raise ValueError(f"Expected GT01-GT21 exactly once; found {sorted(records)}")
    return records


def flatten_catalogue_skills(catalogue: dict[str, Any]) -> list[dict[str, Any]]:
    if catalogue.get("configuration") == "A":
        return catalogue.get("skills", [])
    return [
        skill
        for dept in catalogue.get("departments", [])
        for skill in dept.get("skills", [])
    ]


def resolve_condition(
    repo: Path, experiment: str, configuration: str, size: int
) -> tuple[Path, dict[str, Any], list[str]]:
    if configuration not in ALLOWED_CONFIGURATIONS:
        raise ValueError(
            f"Only C configuration is allowed in the WorkBuddy adapter; got {configuration}"
        )
    if (experiment, size) not in ALLOWED_CONDITIONS:
        raise ValueError(
            "WorkBuddy adapter only allows E0-C-size46, E1-C-size10, "
            f"E1-C-size30, E1-C-size46; got {experiment}-C-size{size}"
        )
    catalogue_path = (
        repo / "skillnet_run_guide_v1_1" / "catalogues"
        / f"size_{size}" / CONFIGURATION_FILENAMES[configuration]
    )
    catalogue = load_json(catalogue_path)
    if catalogue.get("configuration") != configuration:
        raise ValueError(f"Catalogue configuration mismatch: {catalogue_path}")
    if catalogue.get("catalogue_size") != size:
        raise ValueError(f"Catalogue size mismatch: {catalogue_path}")
    skill_ids = [item.get("skill_id") for item in flatten_catalogue_skills(catalogue)]
    if len(skill_ids) != size or len(set(skill_ids)) != size:
        raise ValueError(f"Catalogue wrong/duplicate Skill IDs: {catalogue_path}")

    prompts = load_prompt_map(repo)
    if experiment == "E0":
        task_ids = sorted(prompts, key=lambda tid: int(tid[2:4]))
    else:
        manifest = load_json(repo / "skillnet_run_guide_v1_1" / "E1_scale_manifest.json")
        task_ids = manifest.get("task_ids", [])
        if not isinstance(task_ids, list) or len(task_ids) != 5:
            raise ValueError("E1 manifest must contain exactly five task_ids")
        for tid in task_ids:
            if tid not in prompts:
                raise ValueError(f"E1 manifest references missing prompt: {tid}")
    return catalogue_path, catalogue, task_ids


def canonical_schema_path(repo: Path) -> Path:
    return repo / "SkillNet_Gold_Tasks_V4" / "evaluation" / "prediction_schema.json"


def schema_errors(
    prediction: Any, schema: dict[str, Any], expected_task_id: str
) -> list[dict[str, str]]:
    errors = [
        {"path": ".".join(str(p) for p in e.absolute_path), "message": e.message}
        for e in sorted(
            Draft202012Validator(schema).iter_errors(prediction),
            key=lambda x: list(x.absolute_path),
        )
    ]
    if isinstance(prediction, dict) and prediction.get("task_id") != expected_task_id:
        errors.append({
            "path": "task_id",
            "message": (
                f"task_id must equal {expected_task_id!r}; "
                f"received {prediction.get('task_id')!r}"
            ),
        })
    return errors


def validate_direct_response(
    raw_path: Path, schema: dict[str, Any], expected_task_id: str
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    report: dict[str, Any] = {
        "task_id": expected_task_id,
        "raw_response_exists": raw_path.is_file(),
        "direct_json_parse": False,
        "schema_valid": False,
        "task_id_match": False,
        "errors": [],
    }
    if not raw_path.is_file():
        report["errors"].append({"path": "", "message": "raw_response.txt was not produced"})
        return report, None
    raw = raw_path.read_text(encoding="utf-8")
    try:
        prediction = json.loads(raw)
        report["direct_json_parse"] = True
    except json.JSONDecodeError as exc:
        report["errors"].append({
            "path": "",
            "message": f"raw response is not directly parseable JSON: {exc}",
        })
        return report, None
    if not isinstance(prediction, dict):
        report["errors"].append({"path": "", "message": "prediction must be a JSON object"})
        return report, None
    errors = schema_errors(prediction, schema, expected_task_id)
    report["errors"] = errors
    report["task_id_match"] = prediction.get("task_id") == expected_task_id
    report["schema_valid"] = not errors
    return report, prediction if not errors else None


# ── Child prompt assembly (byte-identical contract to frozen runner) ─────


def build_child_prompt(task_id: str, prompt_zh: str, catalogue: dict[str, Any]) -> str:
    catalogue_text = json.dumps(catalogue, ensure_ascii=False, indent=2)
    return f"""你正在完成一个隔离的 SkillNet 路由任务。

严格限制：
- 不要调用任何工具，不要读取文件，不要检查仓库或外部信息。
- 只能使用下方“当前中文任务”和“当前唯一 Catalogue”。
- 不得假设或使用 Catalogue 之外的 Skill。
- 只进行路由预测，不执行任何业务动作。
- 只返回一个满足下方固定输出契约的 JSON 对象。
- 不要输出 Markdown、代码围栏、解释性前后缀或第二次答案。
- task_id 必须是 `{task_id}`。
- skill_sequence 和 blocked_by 只能使用当前 Catalogue 中的 canonical skill_id。
- selected_departments 只能使用当前 Catalogue 中的 canonical department_id。

固定输出契约（八个字段必须全部出现，不得增加其他字段）：
- task_id：字符串，值必须是 `{task_id}`。
- use_skills：布尔值。
- selected_departments：无重复字符串数组。
- skill_sequence：无重复字符串数组，按执行顺序排列。
- final_status：字符串，只能是 completed、blocked 或 no_tool。
- blocked_by：无重复字符串数组。
- route_choice：JSON 对象；每个键和值都必须是字符串。
- reason：非空字符串，简洁说明路由判断。

状态一致性规则：
- completed：use_skills 为 true，blocked_by 为空数组。
- blocked：use_skills 为 true，blocked_by 至少包含一个当前 Catalogue 的 canonical skill_id。
- no_tool：use_skills 为 false，selected_departments、skill_sequence、blocked_by 都为空数组。

当前中文任务：
{prompt_zh}

当前唯一 Catalogue：
{catalogue_text}
"""


# ── Path helpers ────────────────────────────────────────────────────────


def default_state_root(model_slug: str) -> Path:
    return Path(__file__).resolve().parent / model_slug


def condition_run_root(
    state_root: Path, experiment: str, configuration: str, size: int, run_id: str
) -> Path:
    return state_root / "runs" / experiment / configuration / f"size_{size}" / run_id


def expected_run_artifacts(schema_validation: dict[str, Any]) -> list[str]:
    artifacts = list(RUN_REQUIRED_ARTIFACTS)
    if schema_validation.get("schema_valid") is True:
        artifacts.append("prediction.json")
    return artifacts


# ── Packet manifest ────────────────────────────────────────────────────


def build_packet_manifest(
    *, repo: Path, experiment: str, configuration: str, size: int, run_id: str,
    task_id: str, prompt_record: dict[str, str], child_prompt_sha256: str,
    catalogue_path: Path, catalogue_source_sha256: str,
    catalogue_embedded_sha256: str, catalogue_snapshot_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0-wb",
        "experiment_id": experiment,
        "task_id": task_id,
        "configuration": configuration,
        "catalogue_size": size,
        "run_id": run_id,
        "delivery": {
            "child_prompt": "stdin",
            "raw_response": "codebuddy --print stdout (text)",
            "cli_events": "codebuddy --print stdout bytes",
        },
        "child_working_directory": {
            "temporary": True,
            "contents_at_launch": [],
            "symlinks": [],
        },
        "child_visible_inputs": [
            "current_chinese_task",
            "selected_catalogue",
            "fixed_prediction_json_contract",
            "non_answer_metadata",
        ],
        "child_hidden_inputs": [
            "Gold",
            "deterministic_evaluator",
            "canonical_Skills",
            "other_tasks",
            "other_catalogues",
            "standalone_relations",
            "prior_results",
        ],
        "inputs": {
            "task_prompt": {
                "source": prompt_record["source"],
                "source_sha256": prompt_record["sha256"],
                "text_zh": prompt_record["prompt_zh"],
            },
            "catalogue": {
                "source": str(catalogue_path.relative_to(repo)),
                "source_sha256": catalogue_source_sha256,
                "embedded_json_sha256": catalogue_embedded_sha256,
                "snapshot_sha256": catalogue_snapshot_sha256,
            },
            "child_prompt": {
                "sha256": child_prompt_sha256,
                "assembled_by": str(Path(__file__).resolve().relative_to(repo)),
                "assembler_sha256": sha256_file(Path(__file__).resolve()),
            },
        },
    }


# ── Execution ──────────────────────────────────────────────────────────


def execute_codebuddy(
    cli: Path,
    prompt: str,
    *,
    model_id: str,
    system_prompt_file: Path,
    packet_dir: Path,
    events_path: Path,
    raw_path: Path,
) -> tuple[int, bytes, str, bool, list[str], str, int]:
    """One fresh, non-interactive codebuddy process. One attempt. New UUID.

    Uses Popen so the real child PID is recorded in run_metadata, as the
    contract requires. stdout is preserved byte-for-byte.
    """
    session_id = str(uuid.uuid4())
    command: list[str] = cli_invocation(cli) + [
        "--print",
        "--output-format", "text",
        "--tools", "",                 # disable all built-in tools
        "--strict-mcp-config",         # ignore all MCP configs (no --mcp-config passed)
        "--system-prompt-file", str(system_prompt_file),  # override default prompt -> isolate memory
        "--session-id", session_id,    # fresh unique session per task
        "--max-turns", "1",
    ]
    if model_id:
        command += ["--model", model_id]
    # NOTE: --fallback-model is intentionally OMITTED so no fallback occurs.
    # Working directory is the fresh empty packet_dir (no --cd flag exists).
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(packet_dir),
    )
    pid = process.pid
    stdout_bytes, stderr_bytes = process.communicate(input=prompt.encode("utf-8"))
    if isinstance(stdout_bytes, str):
        stdout_bytes = stdout_bytes.encode("utf-8")
    stderr_text = (
        stderr_bytes
        if isinstance(stderr_bytes, str)
        else stderr_bytes.decode("utf-8", errors="replace")
    )
    write_bytes(events_path, stdout_bytes, exclusive=True)
    raw_text = stdout_bytes.decode("utf-8", errors="replace")
    write_bytes(raw_path, raw_text.encode("utf-8"), exclusive=True)
    return (
        process.returncode,
        stdout_bytes,
        stderr_text,
        raw_path.is_file(),
        command,
        session_id,
        pid,
    )


def execute_fixture(
    fixture_dir: Path, task_id: str, raw_path: Path,
    events_path: Path | None = None,
) -> tuple[int, str, str, bool]:
    if events_path is not None:
        write_bytes(events_path, b"", exclusive=True)
    fixture_path = fixture_dir / f"{task_id}.txt"
    if not fixture_path.is_file():
        return 4, "", f"Missing fixture response: {fixture_path}", False
    shutil.copyfile(fixture_path, raw_path)
    return 0, "", "", True


# ── E1-C-size46 derivation from E0-C-size46 (no model call) ─────────────


def derive_e1_size46_from_e0(
    *, state_root: Path, run_id: str, catalogue_path: Path, schema_path: Path,
) -> Path:
    """Copy the 5 E1 Gold task dirs from the E0-C-size46 run into an
    E1-C-size46 run. No model process is started."""
    e0_run_root = condition_run_root(state_root, "E0", "C", 46, run_id)
    e1_run_root = condition_run_root(state_root, "E1", "C", 46, run_id)
    if not e0_run_root.is_dir():
        raise SystemExit(
            f"Cannot derive E1-C-size46: E0-C-size46 run not found: {e0_run_root}"
        )
    if e1_run_root.exists():
        raise SystemExit(f"E1-C-size46 run already exists: {e1_run_root}")
    e0_cond_meta = load_json(e0_run_root / "condition_metadata.json")
    manifest = load_json(
        repository_root() / "skillnet_run_guide_v1_1" / "E1_scale_manifest.json"
    )
    task_ids = manifest.get("task_ids", [])
    if not isinstance(task_ids, list) or len(task_ids) != 5:
        raise SystemExit("E1 manifest must contain exactly five task_ids")

    e1_run_root.mkdir(parents=True)
    cond_meta = {
        "schema_version": "2.0-wb",
        "experiment": "E1",
        "configuration": "C",
        "size": 46,
        "run_id": run_id,
        "task_ids": task_ids,
        "execution_mode": "derived_from_e0_c_size46",
        "derived_from_run": str(e0_run_root),
        "max_workers": 1,
        "attempts_per_task": 0,
        "model_calls_started": 0,
        "transport": e0_cond_meta.get("transport", TRANSPORT_NAME),
        "cli_path": e0_cond_meta.get("cli_path"),
        "cli_version": e0_cond_meta.get("cli_version"),
        "model_id": e0_cond_meta.get("model_id"),
        "model_slug": e0_cond_meta.get("model_slug"),
        "created_at_utc": utc_now(),
        "repository_commit": git_head(repository_root()),
        "catalogue_path": str(catalogue_path.relative_to(repository_root())),
        "catalogue_sha256": sha256_file(catalogue_path),
        "catalogue_source_commit": e0_cond_meta.get("catalogue_source_commit"),
        "prediction_schema_path": str(schema_path.relative_to(repository_root())),
        "prediction_schema_sha256": sha256_file(schema_path),
        "e1_manifest_sha256": sha256_file(
            repository_root() / "skillnet_run_guide_v1_1" / "E1_scale_manifest.json"
        ),
    }
    write_json(e1_run_root / "condition_metadata.json", cond_meta, exclusive=True)

    copied = 0
    for task_id in task_ids:
        src = e0_run_root / task_id
        dst = e1_run_root / task_id
        if not src.is_dir():
            raise SystemExit(f"Cannot derive: E0 task dir missing: {src}")
        shutil.copytree(src, dst)
        # Re-stamp run_metadata so the derived origin is unambiguous.
        meta_path = dst / "run_metadata.json"
        if meta_path.is_file():
            meta = load_json(meta_path)
            meta["experiment_id"] = "E1"
            meta["experiment"] = "E1"
            meta["catalogue_size"] = 46
            meta["size"] = 46
            meta["execution_mode"] = "derived_from_e0_c_size46"
            meta["derived_from_e0_task_dir"] = str(src)
            meta["model_call_started"] = False
            meta_path.unlink()
            write_json(meta_path, meta, exclusive=True)
        copied += 1

    summary = {
        "run_root": str(e1_run_root),
        "execution_mode": "derived_from_e0_c_size46",
        "model_calls_started": 0,
        "task_dirs_copied": copied,
        "task_ids": task_ids,
        "source_run_root": str(e0_run_root),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return e1_run_root


# ── Main ────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", choices=("E0", "E1"), required=True)
    parser.add_argument("--configuration", choices=("C",), required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model-id", default="", help="MODEL_ID passed to codebuddy --model")
    parser.add_argument("--model-slug", default="", help="MODEL_SLUG (per-model state-root)")
    parser.add_argument("--cli-path", type=Path, default=None, help="Explicit codebuddy binary path")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true", help="Real codebuddy child processes")
    mode.add_argument(
        "--fixture-response-dir", type=Path,
        help="SETUP only: static responses instead of codebuddy",
    )
    mode.add_argument(
        "--derive-e1-size46", action="store_true",
        help="E1-C-size46 only: derive from the E0-C-size46 run, no model call",
    )
    parser.add_argument(
        "--state-root", type=Path, default=None,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.configuration not in ALLOWED_CONFIGURATIONS:
        raise SystemExit(f"Only C configuration allowed; got {args.configuration}")
    if (args.experiment, args.size) not in ALLOWED_CONDITIONS:
        raise SystemExit(
            "Only E0-C-size46, E1-C-size10, E1-C-size30, E1-C-size46 allowed; "
            f"got {args.experiment}-C-size{args.size}"
        )
    if not RUN_ID_PATTERN.fullmatch(args.run_id):
        raise SystemExit("run_id must match [A-Za-z0-9][A-Za-z0-9._-]*")

    # E1-C-size46 must be derived, never executed or fixtured.
    if args.experiment == "E1" and args.size == 46:
        if not args.derive_e1_size46:
            raise SystemExit(
                "E1-C-size46 must use --derive-e1-size46 (derived from E0-C-size46); "
                "it must not start model processes."
            )
    if args.derive_e1_size46 and (args.experiment, args.size) != ("E1", 46):
        raise SystemExit("--derive-e1-size46 is only valid for E1-C-size46")

    repo = repository_root()

    # Resolve state-root (per-model isolation).
    if args.state_root is not None:
        state_root = args.state_root.resolve()
    else:
        if not args.model_slug or not MODEL_SLUG_PATTERN.fullmatch(args.model_slug):
            raise SystemExit(
                "--model-slug (lowercase letters/digits/underscore) is required "
                "when --state-root is not given"
            )
        state_root = default_state_root(args.model_slug)

    catalogue_path, catalogue, task_ids = resolve_condition(
        repo, args.experiment, args.configuration, args.size
    )
    schema_path = canonical_schema_path(repo)
    schema = load_json(schema_path)

    # ── E1-C-size46 derivation branch ───────────────────────────────
    if args.derive_e1_size46:
        return 0 if derive_e1_size46_from_e0(
            state_root=state_root, run_id=args.run_id,
            catalogue_path=catalogue_path, schema_path=schema_path,
        ) else 1

    prompts = load_prompt_map(repo)
    run_root = condition_run_root(
        state_root, args.experiment, args.configuration, args.size, args.run_id
    )
    cond_meta_path = run_root / "condition_metadata.json"

    if run_root.exists():
        raise SystemExit(f"Run already exists and will not be overwritten: {run_root}")

    # ── Transport check ─────────────────────────────────────────────
    cli_path: Path | None = None
    cli_ver = "N/A (fixture)"
    if args.execute:
        cli_path = locate_cli(args.cli_path)
        cli_ver = cli_version(cli_path)
        if not child_system_prompt_file().is_file():
            raise SystemExit(
                f"Missing child system prompt file: {child_system_prompt_file()}"
            )

    run_root.mkdir(parents=True)
    catalogue_source_sha256 = sha256_file(catalogue_path)
    catalogue_embedded_bytes = json.dumps(
        catalogue, ensure_ascii=False, indent=2
    ).encode("utf-8")
    schema_sha256 = sha256_file(schema_path)
    cond_meta = {
        "schema_version": "2.0-wb",
        "experiment": args.experiment,
        "configuration": args.configuration,
        "size": args.size,
        "run_id": args.run_id,
        "task_ids": task_ids,
        "execution_mode": "codebuddy" if args.execute else "fixture",
        "max_workers": 1,
        "attempts_per_task": 1,
        "automatic_retries": 0,
        "task_attempt_definition": "one fresh codebuddy --print process",
        "transport": TRANSPORT_NAME if args.execute else "fixture",
        "cli_path": str(cli_path) if cli_path else None,
        "cli_invocation": cli_invocation(cli_path) if cli_path else None,
        "cli_version": cli_ver,
        "model_id": args.model_id or None,
        "model_slug": args.model_slug or None,
        "created_at_utc": utc_now(),
        "repository_commit": git_head(repo),
        "catalogue_path": str(catalogue_path.relative_to(repo)),
        "catalogue_sha256": catalogue_source_sha256,
        "catalogue_source_commit": catalogue.get("source_commit"),
        "prediction_schema_path": str(schema_path.relative_to(repo)),
        "prediction_schema_sha256": schema_sha256,
        "e1_manifest_sha256": (
            sha256_file(repo / "skillnet_run_guide_v1_1" / "E1_scale_manifest.json")
            if args.experiment == "E1" else None
        ),
        "child_isolation": {
            "tools_disabled": "--tools \"\"" if args.execute else None,
            "mcp_disabled": "--strict-mcp-config (no --mcp-config)" if args.execute else None,
            "fallback_disabled": "--fallback-model omitted" if args.execute else None,
            "memory_isolated": "--system-prompt-file override" if args.execute else None,
            "new_session_per_task": "--session-id <uuid>" if args.execute else None,
            "fresh_empty_cwd": "subprocess cwd=tempdir" if args.execute else None,
            "one_attempt_no_resume": True,
        },
        "events_file_note": (
            "Named codex_events.jsonl to match the frozen artifact inventory; "
            "content is codebuddy --print stdout bytes."
        ),
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "jsonschema_version": importlib.metadata.version("jsonschema"),
        },
    }
    write_json(cond_meta_path, cond_meta, exclusive=True)

    completed = 0
    child_failures = 0
    missing_artifacts: dict[str, list[str]] = {}

    for task_id in task_ids:
        task_dir = run_root / task_id
        raw_path = task_dir / "raw_response.txt"
        events_path = task_dir / "codex_events.jsonl"
        prediction_path = task_dir / "prediction.json"
        validation_path = task_dir / "schema_validation.json"
        metadata_path = task_dir / "run_metadata.json"
        packet_manifest_path = task_dir / "packet_manifest.json"
        catalogue_snapshot_path = task_dir / "catalogue_snapshot.json"

        if raw_path.exists():
            raise SystemExit(f"Refusing to overwrite existing raw response: {raw_path}")
        if prediction_path.exists():
            raise SystemExit(
                f"Inconsistent run: prediction exists without raw response: {prediction_path}"
            )
        task_dir.mkdir(parents=True, exist_ok=True)

        prompt = build_child_prompt(task_id, prompts[task_id]["prompt_zh"], catalogue)
        prompt_sha256 = sha256_bytes(prompt.encode("utf-8"))
        write_json(catalogue_snapshot_path, catalogue, exclusive=True)
        catalogue_snapshot_sha256 = sha256_file(catalogue_snapshot_path)
        packet_manifest = build_packet_manifest(
            repo=repo, experiment=args.experiment, configuration=args.configuration,
            size=args.size, run_id=args.run_id, task_id=task_id,
            prompt_record=prompts[task_id], child_prompt_sha256=prompt_sha256,
            catalogue_path=catalogue_path, catalogue_source_sha256=catalogue_source_sha256,
            catalogue_embedded_sha256=sha256_bytes(catalogue_embedded_bytes),
            catalogue_snapshot_sha256=catalogue_snapshot_sha256,
        )
        write_json(packet_manifest_path, packet_manifest, exclusive=True)

        started_dt = datetime.now(timezone.utc)
        started_mono = time.monotonic()
        command: list[str] | None = None
        session_id_used: str | None = None
        pid: int | None = None

        if args.fixture_response_dir:
            fixture_path = args.fixture_response_dir.resolve() / f"{task_id}.txt"
            command = ["fixture-copy", str(fixture_path), str(raw_path)]
            rc, _stdout, stderr, raw_produced = execute_fixture(
                args.fixture_response_dir.resolve(), task_id, raw_path, events_path
            )
        else:
            assert cli_path is not None
            with tempfile.TemporaryDirectory(prefix=f"wb_{task_id}_") as packet:
                packet_dir = Path(packet)
                (
                    rc, _stdout, stderr, raw_produced,
                    command, session_id_used, pid,
                ) = execute_codebuddy(
                    cli_path, prompt,
                    model_id=args.model_id,
                    system_prompt_file=child_system_prompt_file(),
                    packet_dir=packet_dir,
                    events_path=events_path,
                    raw_path=raw_path.resolve(),
                )
        finished_mono = time.monotonic()
        finished_dt = datetime.now(timezone.utc)

        if not events_path.exists():
            write_bytes(events_path, b"", exclusive=True)
        raw_response_placeholder = not raw_path.exists()
        if raw_response_placeholder:
            write_bytes(raw_path, b"", exclusive=True)

        validation, prediction = validate_direct_response(raw_path, schema, task_id)
        validation.update({
            "raw_response_sha256": sha256_file(raw_path),
            "prediction_saved": prediction is not None,
        })
        write_json(validation_path, validation, exclusive=True)
        if prediction is not None:
            write_json(prediction_path, prediction, exclusive=True)

        run_metadata = {
            "schema_version": "2.0-wb",
            "experiment_id": args.experiment,
            "experiment": args.experiment,
            "task_id": task_id,
            "configuration": args.configuration,
            "catalogue_size": args.size,
            "size": args.size,
            "run_id": args.run_id,
            "model_slug": args.model_slug or None,
            "runtime_repo_commit": cond_meta["repository_commit"],
            "catalogue_source_commit": catalogue.get("source_commit"),
            "transport": TRANSPORT_NAME if args.execute else "fixture",
            "cli_path": str(cli_path) if cli_path else None,
            "cli_version": cli_ver,
            "model_id": args.model_id or None,
            "session_uuid": session_id_used,
            "system_prompt_file": (
                str(child_system_prompt_file().relative_to(repo))
                if args.execute else None
            ),
            "start_time": started_dt.isoformat(),
            "end_time": finished_dt.isoformat(),
            "duration_seconds": round(finished_mono - started_mono, 6),
            "exit_code": rc,
            "pid": pid,
            "input_hashes": {
                "prompt_source_sha256": prompts[task_id]["sha256"],
                "child_prompt_sha256": prompt_sha256,
                "catalogue_source_sha256": catalogue_source_sha256,
                "catalogue_embedded_json_sha256": sha256_bytes(catalogue_embedded_bytes),
                "catalogue_snapshot_sha256": catalogue_snapshot_sha256,
                "prediction_schema_sha256": schema_sha256,
                "runner_source_sha256": sha256_file(Path(__file__).resolve()),
            },
            "execution_mode": "codebuddy" if args.execute else "fixture",
            "attempt_number": 1,
            "automatic_retry": False,
            "task_attempt_definition": "one fresh codebuddy --print process",
            "prompt_source": prompts[task_id]["source"],
            "catalogue_path": str(catalogue_path.relative_to(repo)),
            "catalogue_sha256": catalogue_source_sha256,
            "command": command,
            "stderr": stderr if args.execute else "",
            "raw_response_produced": raw_produced,
            "raw_response_placeholder": raw_response_placeholder,
            "raw_response_sha256": sha256_file(raw_path),
            "codex_events_sha256": sha256_file(events_path),
            "events_source": "codebuddy --print stdout" if args.execute else "fixture-empty",
            "prediction_saved": prediction is not None,
        }
        write_json(metadata_path, run_metadata, exclusive=True)

        missing = [
            fname for fname in expected_run_artifacts(validation)
            if not (task_dir / fname).is_file()
        ]
        if missing:
            missing_artifacts[task_id] = missing
        if rc != 0:
            child_failures += 1
        completed += 1

    summary = {
        "run_root": str(run_root),
        "task_count": len(task_ids),
        "task_artifact_sets_created": completed,
        "child_process_failures": child_failures,
        "missing_run_artifacts": missing_artifacts,
        "execution_mode": "codebuddy" if args.execute else "fixture",
        "max_workers": 1,
        "attempts_per_task": 1,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if missing_artifacts:
        return 5
    return 0 if child_failures == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
