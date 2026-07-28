#!/usr/bin/env python3
"""Structural contract for the Procurement Codex skill collection."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
EXPECTED_RESOURCES = {
    "procurement-requirement": {"assets/procurement_request_template.md"},
    "procurement-supplier-search": {"assets/supplier_search_template.md"},
    "procurement-supplier-qualification": {
        "assets/supplier_qualification_checklist.md"
    },
    "procurement-rfq-generation": {"assets/rfq_template.md"},
    "procurement-quote-comparison": {"scripts/compare_quotes.py"},
    "procurement-supplier-scoring": {
        "assets/supplier_scorecard.md",
        "scripts/score_suppliers.py",
    },
    "procurement-supplier-selection": {"assets/supplier_selection_memo.md"},
    "procurement-contract-generation": {"assets/contract_draft_template.md"},
    "procurement-purchase-order": {
        "assets/purchase_order_template.md",
        "scripts/render_purchase_order.py",
    },
    "procurement-delivery-tracking": {"assets/delivery_tracking_template.md"},
    "procurement-delivery-acceptance": {
        "assets/delivery_acceptance_template.md"
    },
    "procurement-supplier-evaluation": {"scripts/evaluate_supplier.py"},
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


class ProcurementSkillContractTests(unittest.TestCase):
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
        self.validate_skill("procurement-requirement")

    def test_supplier_search(self):
        self.validate_skill("procurement-supplier-search")

    def test_supplier_qualification(self):
        self.validate_skill("procurement-supplier-qualification")

    def test_rfq_generation(self):
        self.validate_skill("procurement-rfq-generation")

    def test_quote_comparison(self):
        self.validate_skill("procurement-quote-comparison")

    def test_supplier_scoring(self):
        self.validate_skill("procurement-supplier-scoring")

    def test_supplier_selection(self):
        self.validate_skill("procurement-supplier-selection")

    def test_contract_generation(self):
        self.validate_skill("procurement-contract-generation")

    def test_purchase_order(self):
        self.validate_skill("procurement-purchase-order")

    def test_delivery_tracking(self):
        self.validate_skill("procurement-delivery-tracking")

    def test_delivery_acceptance(self):
        self.validate_skill("procurement-delivery-acceptance")

    def test_supplier_evaluation(self):
        self.validate_skill("procurement-supplier-evaluation")

if __name__ == "__main__":
    unittest.main()
