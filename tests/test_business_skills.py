#!/usr/bin/env python3
"""Structural contract for the Business Codex skill collection."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
EXPECTED_RESOURCES = {
    "business-customer-lead": {"assets/customer_lead_template.md"},
    "business-requirement-communication": {
        "assets/requirement_communication_template.md"
    },
    "business-opportunity-assessment": {"scripts/evaluate_opportunity.py"},
    "business-solution-quotation": {
        "assets/solution_quotation_template.md",
        "scripts/calculate_quotation.py",
    },
    "business-negotiation": {"assets/negotiation_record_template.md"},
    "business-contract-signing": {
        "assets/contract_signing_checklist.md",
        "scripts/validate_contract_signing.py",
    },
    "business-project-delivery-tracking": {
        "assets/project_delivery_tracker.md",
        "scripts/evaluate_delivery_progress.py",
    },
    "business-acceptance": {"assets/acceptance_template.md"},
    "business-renewal": {"assets/renewal_template.md"},
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


class BusinessSkillContractTests(unittest.TestCase):
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

    def test_customer_lead(self):
        self.validate_skill("business-customer-lead")

    def test_requirement_communication(self):
        self.validate_skill("business-requirement-communication")

    def test_opportunity_assessment(self):
        self.validate_skill("business-opportunity-assessment")

    def test_solution_quotation(self):
        self.validate_skill("business-solution-quotation")

    def test_negotiation(self):
        self.validate_skill("business-negotiation")

    def test_contract_signing(self):
        self.validate_skill("business-contract-signing")

    def test_project_delivery_tracking(self):
        self.validate_skill("business-project-delivery-tracking")

    def test_acceptance(self):
        self.validate_skill("business-acceptance")

    def test_renewal(self):
        self.validate_skill("business-renewal")


if __name__ == "__main__":
    unittest.main()
