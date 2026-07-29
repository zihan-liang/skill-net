#!/usr/bin/env python3
"""Synchronize every SkillNet Relationships section from skill_relations.json."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Set


EDGE_TYPES = ("conflict", "contains", "enhances", "mutex", "prerequisite")
RELATIONSHIP_HEADING = "## SkillNet Relationships"


class GraphValidationError(ValueError):
    """Raised when skill_relations.json does not match the supported schema."""


def require_keys(
    edge: Mapping[str, Any],
    required: Set[str],
    optional: Set[str],
    location: str,
) -> None:
    keys = set(edge)
    missing = required - keys
    extra = keys - required - optional
    if missing or extra:
        raise GraphValidationError(
            f"{location} has invalid keys; missing={sorted(missing)}, extra={sorted(extra)}"
        )


def require_name(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GraphValidationError(f"{location} must be a non-empty string")
    return value


def require_optional_name(value: Any, location: str) -> str | None:
    if value is None:
        return None
    return require_name(value, location)


def require_pair(value: Any, location: str) -> Sequence[str]:
    if not isinstance(value, list) or len(value) != 2:
        raise GraphValidationError(f"{location} must be a two-item array")
    pair = [require_name(item, f"{location}[{index}]") for index, item in enumerate(value)]
    if pair[0] == pair[1]:
        raise GraphValidationError(f"{location} cannot connect a node to itself")
    return pair


def load_graph(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    graph = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(graph, dict) or set(graph) != set(EDGE_TYPES):
        raise GraphValidationError(
            f"top-level edge types must be exactly {list(EDGE_TYPES)}"
        )
    if not all(isinstance(graph[edge_type], list) for edge_type in EDGE_TYPES):
        raise GraphValidationError("every edge type must contain an array")

    for index, edge in enumerate(graph["contains"]):
        location = f"contains[{index}]"
        if not isinstance(edge, dict):
            raise GraphValidationError(f"{location} must be an object")
        require_keys(edge, {"parent", "children"}, set(), location)
        require_name(edge["parent"], f"{location}.parent")
        children = edge["children"]
        if not isinstance(children, list) or not children:
            raise GraphValidationError(f"{location}.children must be a non-empty array")
        child_names = [
            require_name(child, f"{location}.children[{child_index}]")
            for child_index, child in enumerate(children)
        ]
        if len(child_names) != len(set(child_names)):
            raise GraphValidationError(f"{location}.children contains duplicates")

    for index, edge in enumerate(graph["prerequisite"]):
        location = f"prerequisite[{index}]"
        if not isinstance(edge, dict):
            raise GraphValidationError(f"{location} must be an object")
        require_keys(edge, {"before", "after", "scope"}, {"condition"}, location)
        require_name(edge["before"], f"{location}.before")
        require_name(edge["after"], f"{location}.after")
        require_name(edge["scope"], f"{location}.scope")
        require_optional_name(edge.get("condition"), f"{location}.condition")

    for edge_type, qualifier in (("conflict", "condition"), ("mutex", "context")):
        for index, edge in enumerate(graph[edge_type]):
            location = f"{edge_type}[{index}]"
            if not isinstance(edge, dict):
                raise GraphValidationError(f"{location} must be an object")
            require_keys(edge, {"skills", qualifier}, set(), location)
            require_pair(edge["skills"], f"{location}.skills")
            require_optional_name(edge[qualifier], f"{location}.{qualifier}")

    for index, edge in enumerate(graph["enhances"]):
        location = f"enhances[{index}]"
        if not isinstance(edge, dict):
            raise GraphValidationError(f"{location} must be an object")
        require_keys(edge, {"source", "target", "context"}, set(), location)
        require_name(edge["source"], f"{location}.source")
        require_name(edge["target"], f"{location}.target")
        require_optional_name(edge["context"], f"{location}.context")

    return graph


def discover_skill_paths(skills_root: Path) -> Dict[str, Path]:
    paths = {
        path.parent.name: path
        for path in skills_root.glob("*/SKILL.md")
        if path.is_file()
    }
    if not paths:
        raise GraphValidationError(f"no SKILL.md files found under {skills_root}")
    return paths


def add_line(
    rendered: MutableMapping[str, MutableMapping[str, List[str]]],
    skill: str,
    edge_type: str,
    line: str,
) -> None:
    rendered[skill][edge_type].append(line)


def render_relationships(
    graph: Mapping[str, List[Dict[str, Any]]],
    real_skills: Set[str],
) -> Dict[str, str]:
    rendered: MutableMapping[str, MutableMapping[str, List[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    referenced_nodes: Set[str] = set()

    for group in graph["contains"]:
        parent = group["parent"]
        for child in group["children"]:
            referenced_nodes.update((parent, child))
            if parent in real_skills:
                add_line(rendered, parent, "contains", f"Contains `{child}`.")
            if child in real_skills:
                add_line(rendered, child, "contains", f"Part of `{parent}`.")

    for edge in graph["prerequisite"]:
        before, after = edge["before"], edge["after"]
        referenced_nodes.update((before, after))
        condition = edge.get("condition")
        suffix = f" when `{condition}`." if condition is not None else "."
        if before in real_skills:
            add_line(rendered, before, "prerequisite", f"Precedes `{after}`{suffix}")
        if after in real_skills:
            add_line(rendered, after, "prerequisite", f"Follows `{before}`{suffix}")

    for edge in graph["conflict"]:
        left, right = edge["skills"]
        referenced_nodes.update((left, right))
        condition = edge["condition"]
        suffix = f" when `{condition}`." if condition is not None else "."
        if left in real_skills:
            add_line(rendered, left, "conflict", f"Blocks `{right}`{suffix}")
        if right in real_skills:
            add_line(rendered, right, "conflict", f"Blocked by `{left}`{suffix}")

    for edge in graph["mutex"]:
        left, right = edge["skills"]
        referenced_nodes.update((left, right))
        context = edge["context"]
        suffix = f" when `{context}`." if context is not None else "."
        if left in real_skills:
            add_line(
                rendered,
                left,
                "mutex",
                f"Must not run with `{right}` in the same session{suffix}",
            )
        if right in real_skills:
            add_line(
                rendered,
                right,
                "mutex",
                f"Must not run with `{left}` in the same session{suffix}",
            )

    for edge in graph["enhances"]:
        source, target, context = edge["source"], edge["target"], edge["context"]
        referenced_nodes.update((source, target))
        if context is None:
            source_line = f"Enhances `{target}`."
            target_line = f"Enhanced by `{source}`."
        else:
            source_line = f"Enhances `{target}` when `{context}`."
            target_line = f"Enhanced by `{source}` when `{context}`."
        if source in real_skills:
            add_line(rendered, source, "enhances", source_line)
        if target in real_skills:
            add_line(rendered, target, "enhances", target_line)

    unknown_nodes = referenced_nodes - real_skills
    contains_parents = {group["parent"] for group in graph["contains"]}
    invalid_unknown = unknown_nodes - contains_parents
    if invalid_unknown:
        raise GraphValidationError(
            f"graph references nodes with no SKILL.md: {sorted(invalid_unknown)}"
        )

    output = {}
    for skill in sorted(real_skills):
        lines: List[str] = []
        for edge_type in EDGE_TYPES:
            lines.extend(f"- {line}" for line in sorted(set(rendered[skill][edge_type])))
        if not lines:
            raise GraphValidationError(f"{skill} has no incident graph relationships")
        output[skill] = "\n".join(lines)
    return output


def replace_relationship_body(text: str, rendered_body: str, source: Path) -> str:
    heading = f"{RELATIONSHIP_HEADING}\n"
    try:
        start = text.index(heading) + len(heading)
        end = text.index("\n## ", start)
    except ValueError as exc:
        raise GraphValidationError(
            f"{source} must contain {RELATIONSHIP_HEADING!r} followed by another level-two heading"
        ) from exc
    return text[:start] + "\n" + rendered_body + "\n" + text[end:]


def synchronize(repo_root: Path, check: bool = False) -> List[Path]:
    graph_path = repo_root / "skill_relations.json"
    skills_root = repo_root / ".agents" / "skills"
    graph = load_graph(graph_path)
    paths = discover_skill_paths(skills_root)
    rendered = render_relationships(graph, set(paths))
    changed = []

    for skill, path in sorted(paths.items()):
        current = path.read_text(encoding="utf-8")
        updated = replace_relationship_body(current, rendered[skill], path)
        if updated == current:
            continue
        changed.append(path)
        if not check:
            path.write_text(updated, encoding="utf-8")

    return changed


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root containing skill_relations.json and .agents/skills",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without writing files and return a non-zero exit status",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    try:
        changed = synchronize(repo_root, check=args.check)
    except (GraphValidationError, json.JSONDecodeError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")

    action = "Would update" if args.check else "Updated"
    print(f"{action} {len(changed)} files.")
    for path in changed:
        print(f"- {display_path(path, repo_root)}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
