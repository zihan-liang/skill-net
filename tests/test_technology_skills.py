#!/usr/bin/env python3
"""Structural contract for the Technology Codex skill collection."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
EXPECTED_RESOURCES = {
    "technology-requirement": {"assets/technology_requirement_template.md"},
    "technology-feasibility-assessment": {
        "assets/feasibility_assessment_template.md"
    },
    "technology-specification-confirmation": {
        "assets/technology_specification_template.md"
    },
    "technology-solution-design": {"assets/technical_design_template.md"},
    "technology-task-breakdown": {"scripts/validate_task_plan.py"},
    "technology-development-implementation": {
        "assets/implementation_record_template.md"
    },
    "technology-test-acceptance": {"scripts/evaluate_test_acceptance.py"},
    "technology-system-release": {
        "assets/release_runbook_template.md",
        "scripts/validate_release_manifest.py",
    },
    "technology-operations-maintenance": {
        "assets/incident_maintenance_template.md"
    },
}
REQUIRED_HEADINGS = {
    "## Overview",
    "## Required Inputs",
    "## Workflow",
    "## Output Contract",
    "## SkillNet Relationships",
    "## Approval Controls",
    "## Exception Handling",
    "## Handoff",
    "## Example",
    "## Common Mistakes",
}


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"')
    return metadata


class TechnologySkillContractTests(unittest.TestCase):
    def validate_skill(self, name: str) -> None:
        folder = SKILLS / name
        skill_file = folder / "SKILL.md"
        agent_file = folder / "agents" / "openai.yaml"

        self.assertTrue(skill_file.is_file(), f"{name}: missing SKILL.md")
        self.assertTrue(agent_file.is_file(), f"{name}: missing agents/openai.yaml")

        text = skill_file.read_text(encoding="utf-8")
        metadata = parse_frontmatter(text)
        self.assertEqual(set(metadata), {"name", "description"})
        self.assertEqual(metadata.get("name"), name)
        self.assertTrue(metadata.get("description", "").startswith("Use when "))
        self.assertFalse(REQUIRED_HEADINGS - set(text.splitlines()))
        self.assertIn("**中文摘要：**", text)
        self.assertIsNone(re.search(r"\bTODO\b|\bTBD\b|\[TODO", text))
        self.assertLess(len(text.split()), 500)
        self.assertTrue(
            "Human approval" in text or "Human confirmation" in text,
            f"{name}: missing human decision boundary",
        )

        for resource in EXPECTED_RESOURCES[name]:
            self.assertTrue((folder / resource).is_file(), f"{name}: missing {resource}")
            self.assertIn(resource, text, f"{name}: does not reference {resource}")

        agent_text = agent_file.read_text(encoding="utf-8")
        self.assertIn(f"${name}", agent_text)

    def test_requirement(self):
        self.validate_skill("technology-requirement")

    def test_feasibility_assessment(self):
        self.validate_skill("technology-feasibility-assessment")

    def test_specification_confirmation(self):
        self.validate_skill("technology-specification-confirmation")

    def test_solution_design(self):
        self.validate_skill("technology-solution-design")

    def test_task_breakdown(self):
        self.validate_skill("technology-task-breakdown")

    def test_development_implementation(self):
        self.validate_skill("technology-development-implementation")

    def test_test_acceptance(self):
        self.validate_skill("technology-test-acceptance")

    def test_system_release(self):
        self.validate_skill("technology-system-release")

    def test_operations_maintenance(self):
        self.validate_skill("technology-operations-maintenance")

if __name__ == "__main__":
    unittest.main()
