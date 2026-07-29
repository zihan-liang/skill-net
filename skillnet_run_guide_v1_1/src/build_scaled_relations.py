#!/usr/bin/env python3
"""Build closed 10/30/46 SkillNet relation files for E1.

The script filters a full skill_relations.json by an allowed skill-ID set.
It validates that the result contains no reference to a skill outside that set.
Only the Python standard library is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def full_skill_ids(relations: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for group in relations.get("contains", []):
        ids.extend(group.get("children", []))
    # Preserve first occurrence while detecting duplicates later.
    return list(dict.fromkeys(ids))


def prune_relations(relations: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "contains": [],
        "prerequisite": [],
        "conflict": [],
        "mutex": [],
        "enhances": [],
    }

    for group in relations.get("contains", []):
        children = [skill for skill in group.get("children", []) if skill in allowed]
        if children:
            new_group = dict(group)
            new_group["children"] = children
            result["contains"].append(new_group)

    for edge in relations.get("prerequisite", []):
        if edge.get("before") in allowed and edge.get("after") in allowed:
            result["prerequisite"].append(edge)

    for edge in relations.get("conflict", []):
        skills = edge.get("skills", [])
        if skills and all(skill in allowed for skill in skills):
            result["conflict"].append(edge)

    for edge in relations.get("mutex", []):
        skills = edge.get("skills", [])
        if skills and all(skill in allowed for skill in skills):
            result["mutex"].append(edge)

    for edge in relations.get("enhances", []):
        if edge.get("source") in allowed and edge.get("target") in allowed:
            result["enhances"].append(edge)

    return result


def iter_skill_refs(relations: dict[str, Any]) -> Iterable[str]:
    for group in relations.get("contains", []):
        yield from group.get("children", [])
    for edge in relations.get("prerequisite", []):
        yield edge.get("before", "")
        yield edge.get("after", "")
    for key in ("conflict", "mutex"):
        for edge in relations.get(key, []):
            yield from edge.get("skills", [])
    for edge in relations.get("enhances", []):
        yield edge.get("source", "")
        yield edge.get("target", "")


def validate_closed(relations: dict[str, Any], allowed: set[str]) -> list[str]:
    errors: list[str] = []
    refs = [ref for ref in iter_skill_refs(relations) if ref]
    outside = sorted(set(refs) - allowed)
    if outside:
        errors.append(f"References outside allowed set: {outside}")

    contained = []
    for group in relations.get("contains", []):
        contained.extend(group.get("children", []))
    duplicates = sorted({x for x in contained if contained.count(x) > 1})
    if duplicates:
        errors.append(f"Duplicate contains children: {duplicates}")
    missing = sorted(allowed - set(contained))
    if missing:
        errors.append(f"Allowed skills missing from contains: {missing}")
    return errors


def summary(relations: dict[str, Any]) -> dict[str, int]:
    return {
        "skills": sum(len(group.get("children", [])) for group in relations.get("contains", [])),
        "departments_with_skills": len(relations.get("contains", [])),
        "prerequisite": len(relations.get("prerequisite", [])),
        "conflict": len(relations.get("conflict", [])),
        "mutex": len(relations.get("mutex", [])),
        "enhances": len(relations.get("enhances", [])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    full = load_json(args.relations)
    manifest = load_json(args.manifest)
    all_ids = full_skill_ids(full)
    all_set = set(all_ids)

    if len(all_ids) != 46:
        raise SystemExit(f"Expected 46 unique skills in full relations, found {len(all_ids)}")

    sets: dict[str, list[str]] = dict(manifest["skill_sets"])
    sets["46"] = all_ids

    errors: list[str] = []
    for size, ids in sets.items():
        duplicates = sorted({x for x in ids if ids.count(x) > 1})
        unknown = sorted(set(ids) - all_set)
        if duplicates:
            errors.append(f"size {size}: duplicate IDs {duplicates}")
        if unknown:
            errors.append(f"size {size}: unknown IDs {unknown}")
        if len(ids) != int(size):
            errors.append(f"size {size}: expected {size} IDs, found {len(ids)}")

    if not set(sets["10"]) < set(sets["30"]):
        errors.append("10-skill set is not a strict subset of 30-skill set")
    if not set(sets["30"]) < set(sets["46"]):
        errors.append("30-skill set is not a strict subset of 46-skill set")

    report: dict[str, Any] = {
        "source_relations": str(args.relations),
        "manifest": str(args.manifest),
        "valid": False,
        "sets": {},
        "errors": errors,
    }

    for size in ("10", "30", "46"):
        allowed = set(sets[size])
        pruned = prune_relations(full, allowed)
        closed_errors = validate_closed(pruned, allowed)
        errors.extend(f"size {size}: {e}" for e in closed_errors)
        output_path = args.out_dir / f"skill_relations_{size}.json"
        dump_json(output_path, pruned)
        report["sets"][size] = {
            "output": str(output_path),
            "summary": summary(pruned),
            "outside_reference_count": len(set(iter_skill_refs(pruned)) - allowed),
        }

    report["valid"] = not errors
    report["errors"] = errors
    report_path = args.out_dir / "scale_relations_validation_report.json"
    dump_json(report_path, report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
