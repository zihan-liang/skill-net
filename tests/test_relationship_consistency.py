import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "skill_relations.json"
SKILLS_ROOT = ROOT / ".agents" / "skills"
GENERATOR_PATH = ROOT / "scripts" / "generate_relationships.py"
RELATIONSHIP_HEADING = "## SkillNet Relationships"

BEHAVIOR_CONFLICT_LINES = {
    "hr-jd-generator": (
        "- Conflicts with publication when mandatory facts or headcount approval are missing."
    ),
    "hr-offer-generator": (
        "- Conflicts with generation when compensation or offer approval is absent."
    ),
    "hr-job-requirement": (
        "- Conflicts with publishing or screening when headcount approval is absent."
    ),
    "hr-resume-screening": (
        "- Conflicts with demographic, photo, family-status, or other "
        "protected-characteristic scoring."
    ),
    "hr-recruitment-publish": (
        "- Conflicts with external publication when headcount, JD, channel, or budget "
        "approval is missing."
    ),
}


def load_graph(path=GRAPH_PATH):
    return json.loads(path.read_text(encoding="utf-8"))


def skill_paths(root=SKILLS_ROOT):
    return {
        path.parent.name: path
        for path in root.glob("*/SKILL.md")
        if path.is_file()
    }


def split_relationship_section(text):
    heading = f"{RELATIONSHIP_HEADING}\n"
    start = text.index(heading) + len(heading)
    end = text.index("\n## ", start)
    return text[:start], text[start:end], text[end:]


def graph_nodes_and_incidents(graph):
    nodes = set()
    incidents = {}

    def connect(left, right):
        nodes.update((left, right))
        incidents.setdefault(left, set()).add(right)
        incidents.setdefault(right, set()).add(left)

    for group in graph["contains"]:
        for child in group["children"]:
            connect(group["parent"], child)
    for edge in graph["prerequisite"]:
        connect(edge["before"], edge["after"])
    for edge_type in ("conflict", "mutex"):
        for edge in graph[edge_type]:
            connect(*edge["skills"])
    for edge in graph["enhances"]:
        connect(edge["source"], edge["target"])
    return nodes, incidents


def load_generator():
    if not GENERATOR_PATH.is_file():
        raise AssertionError("scripts/generate_relationships.py must exist")
    spec = importlib.util.spec_from_file_location("generate_relationships", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RelationshipConsistencyTests(unittest.TestCase):
    def test_relationship_sections_exactly_match_deterministic_rendering(self):
        generator = load_generator()
        paths = skill_paths()
        expected = generator.render_relationships(load_graph(), set(paths))
        mismatches = {}

        for skill, path in paths.items():
            _, body, _ = split_relationship_section(path.read_text(encoding="utf-8"))
            actual = body.strip()
            if actual != expected[skill]:
                mismatches[skill] = {"expected": expected[skill], "actual": actual}

        self.assertEqual(mismatches, {})

    def test_conflict_edges_preserve_guard_to_blocked_direction(self):
        generator = load_generator()
        rendered = generator.render_relationships(load_graph(), set(skill_paths()))

        self.assertIn(
            "- Blocks `procurement-purchase-order` when `budget_not_approved`.",
            rendered["finance-budget-check"],
        )
        self.assertNotIn(
            "- Blocked by `procurement-purchase-order` when `budget_not_approved`.",
            rendered["finance-budget-check"],
        )
        self.assertIn(
            "- Blocked by `hr-job-requirement` when `job_criteria_missing`.",
            rendered["hr-resume-screening"],
        )

    def test_prerequisite_conditions_and_mutex_contexts_are_not_dropped(self):
        generator = load_generator()
        graph = load_graph()
        rendered = generator.render_relationships(graph, set(skill_paths()))
        missing = []

        for edge in graph["prerequisite"]:
            condition = edge.get("condition")
            if condition is None:
                continue
            for endpoint in (edge["before"], edge["after"]):
                if f"`{condition}`" not in rendered[endpoint]:
                    missing.append(("prerequisite", endpoint, condition))

        for edge in graph["mutex"]:
            context = edge.get("context")
            if context is None:
                continue
            for endpoint in edge["skills"]:
                if f"`{context}`" not in rendered[endpoint]:
                    missing.append(("mutex", endpoint, context))

        self.assertEqual(missing, [])

    def test_relationship_mentions_exactly_match_incident_graph_nodes(self):
        graph = load_graph()
        nodes, incidents = graph_nodes_and_incidents(graph)
        mismatches = {}

        for skill, path in skill_paths().items():
            _, body, _ = split_relationship_section(path.read_text(encoding="utf-8"))
            mentioned = {token for token in re.findall(r"`([^`]+)`", body) if token in nodes}
            expected = incidents.get(skill, set())
            if mentioned != expected:
                mismatches[skill] = {
                    "missing": sorted(expected - mentioned),
                    "extra": sorted(mentioned - expected),
                }

        self.assertEqual(mismatches, {})

    def test_virtual_parent_nodes_do_not_require_skill_files(self):
        graph = load_graph()
        nodes, _ = graph_nodes_and_incidents(graph)
        real_skills = set(skill_paths())
        virtual_nodes = nodes - real_skills

        self.assertEqual(len(real_skills), 46)
        self.assertEqual(
            virtual_nodes,
            {
                "business-agent",
                "finance-agent",
                "hr-agent",
                "procurement-agent",
                "technology-agent",
            },
        )
        self.assertTrue(all(not (SKILLS_ROOT / node / "SKILL.md").exists() for node in virtual_nodes))

    def test_behavior_conflict_lines_are_relocated_outside_relationships(self):
        failures = {}
        for skill, line in BEHAVIOR_CONFLICT_LINES.items():
            text = skill_paths()[skill].read_text(encoding="utf-8")
            prefix, body, suffix = split_relationship_section(text)
            outside = prefix + suffix
            if line in body or line not in outside:
                failures[skill] = {
                    "still_in_relationships": line in body,
                    "missing_outside_relationships": line not in outside,
                }

        self.assertEqual(failures, {})

    def test_generator_is_idempotent_and_preserves_non_relationship_text(self):
        load_generator()
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            shutil.copy2(GRAPH_PATH, temporary_root / "skill_relations.json")
            shutil.copytree(SKILLS_ROOT, temporary_root / ".agents" / "skills")
            before = {
                skill: split_relationship_section(path.read_text(encoding="utf-8"))
                for skill, path in skill_paths(temporary_root / ".agents" / "skills").items()
            }

            first = subprocess.run(
                [
                    "python3",
                    str(GENERATOR_PATH),
                    "--repo-root",
                    str(temporary_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            after_first = {
                skill: split_relationship_section(path.read_text(encoding="utf-8"))
                for skill, path in skill_paths(temporary_root / ".agents" / "skills").items()
            }
            for skill in before:
                self.assertEqual(after_first[skill][0], before[skill][0])
                self.assertEqual(after_first[skill][2], before[skill][2])

            second = subprocess.run(
                [
                    "python3",
                    str(GENERATOR_PATH),
                    "--repo-root",
                    str(temporary_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("Updated 0 files.", second.stdout)

            drift_path = temporary_root / ".agents" / "skills" / "finance-budget-check" / "SKILL.md"
            drift_text = drift_path.read_text(encoding="utf-8").replace(
                "- Part of `finance-agent`.",
                "- Manually edited relationship.",
                1,
            )
            drift_path.write_text(drift_text, encoding="utf-8")
            check = subprocess.run(
                [
                    "python3",
                    str(GENERATOR_PATH),
                    "--repo-root",
                    str(temporary_root),
                    "--check",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(check.returncode, 1, check.stderr)
            self.assertIn("Would update 1 files.", check.stdout)
            self.assertEqual(drift_path.read_text(encoding="utf-8"), drift_text)


if __name__ == "__main__":
    unittest.main()
