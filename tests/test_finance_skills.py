#!/usr/bin/env python3
"""Structural contract for the Finance Codex skill collection."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED_RESOURCES = {
    "finance-budget-planning": {"assets/budget_template.md"},
    "finance-expense-request": {"assets/expense_request_template.md"},
    "finance-expense-review": set(),
    "finance-invoice-verification": {"scripts/verify_invoice.py"},
    "finance-payment-approval": {"assets/payment_approval_template.md"},
    "finance-accounting": {"scripts/validate_journal.py"},
    "finance-reporting": {"scripts/generate_financial_report.py"},
    "finance-database": {
        "scripts/finance_db.py",
        "references/finance_schema.md",
    },
}
REQUIRED_HEADINGS = {
    "## Overview",
    "## Required Inputs",
    "## Workflow",
    "## Output Contract",
    "## SkillNet Relationships",
    "## Guardrails",
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


class FinanceSkillContractTests(unittest.TestCase):
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

    def test_budget_planning(self):
        self.validate_skill("finance-budget-planning")

    def test_expense_request(self):
        self.validate_skill("finance-expense-request")

    def test_expense_review(self):
        self.validate_skill("finance-expense-review")

    def test_invoice_verification(self):
        self.validate_skill("finance-invoice-verification")

    def test_payment_approval(self):
        self.validate_skill("finance-payment-approval")

    def test_accounting(self):
        self.validate_skill("finance-accounting")

    def test_reporting(self):
        self.validate_skill("finance-reporting")

    def test_database(self):
        self.validate_skill("finance-database")


if __name__ == "__main__":
    unittest.main()
