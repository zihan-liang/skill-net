from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"

EXPECTED_BY_DEPARTMENT = {
    "finance": {
        "finance-budget-planning",
        "finance-budget-check",
        "finance-expense-request",
        "finance-expense-review",
        "finance-invoice-verification",
        "finance-payment-approval",
        "finance-accounting",
        "finance-reporting",
    },
    "procurement": {
        "procurement-requirement",
        "procurement-supplier-search",
        "procurement-supplier-qualification",
        "procurement-rfq-generation",
        "procurement-quote-comparison",
        "procurement-supplier-scoring",
        "procurement-supplier-selection",
        "procurement-contract-generation",
        "procurement-purchase-order",
        "procurement-delivery-tracking",
        "procurement-delivery-acceptance",
        "procurement-supplier-evaluation",
    },
    "technology": {
        "technology-requirement",
        "technology-feasibility-assessment",
        "technology-specification-confirmation",
        "technology-solution-design",
        "technology-task-breakdown",
        "technology-development-implementation",
        "technology-test-acceptance",
        "technology-system-release",
        "technology-operations-maintenance",
    },
    "business": {
        "business-customer-lead",
        "business-requirement-communication",
        "business-opportunity-assessment",
        "business-solution-quotation",
        "business-negotiation",
        "business-contract-signing",
        "business-project-delivery-tracking",
        "business-acceptance",
        "business-renewal",
    },
    "hr": {
        "hr-job-requirement",
        "hr-jd-generator",
        "hr-recruitment-publish",
        "hr-resume-screening",
        "hr-interview-scheduling",
        "hr-offer-generator",
        "hr-onboarding",
        "hr-employee-database",
    },
}

EXPECTED = set().union(*EXPECTED_BY_DEPARTMENT.values())
RETIRED_NAMES = {
    "-".join(parts)
    for parts in (
        ("finance", "database"),
        ("procurement", "budget", "confirmation"),
        ("procurement", "contract", "order"),
        ("procurement", "supplier", "database"),
        ("procurement", "supplier", "sourcing"),
        ("technology", "database"),
        ("business", "acceptance", "renewal"),
        ("business", "customer", "database"),
    )
}
REQUIRED_HEADINGS = {
    "## Required Inputs",
    "## Workflow",
    "## Output Contract",
    "## Approval Controls",
    "## Exception Handling",
    "## Handoff",
}
PROCESS_CHAINS = {
    "procurement": (
        "procurement-requirement",
        "finance-budget-check",
        "procurement-supplier-search",
        "procurement-supplier-qualification",
        "procurement-rfq-generation",
        "procurement-quote-comparison",
        "procurement-supplier-scoring",
        "procurement-supplier-selection",
        "procurement-contract-generation",
        "procurement-purchase-order",
        "procurement-delivery-tracking",
        "procurement-delivery-acceptance",
        "finance-invoice-verification",
        "finance-payment-approval",
        "procurement-supplier-evaluation",
    ),
    "technology": (
        "technology-requirement",
        "technology-feasibility-assessment",
        "technology-specification-confirmation",
        "technology-solution-design",
        "technology-task-breakdown",
        "technology-development-implementation",
        "technology-test-acceptance",
        "technology-system-release",
        "technology-operations-maintenance",
    ),
    "business": (
        "business-customer-lead",
        "business-requirement-communication",
        "business-opportunity-assessment",
        "business-solution-quotation",
        "business-negotiation",
        "business-contract-signing",
        "business-project-delivery-tracking",
        "business-acceptance",
        "business-renewal",
    ),
}


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"{path}: missing opening YAML delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError(f"{path}: missing closing YAML delimiter") from exc

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise AssertionError(f"{path}: invalid YAML line: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or not value:
            raise AssertionError(f"{path}: empty YAML key/value: {line!r}")
        if key in fields:
            raise AssertionError(f"{path}: duplicate YAML key: {key}")
        fields[key] = value
    return fields


class AtomicSkillCatalogTests(unittest.TestCase):
    def test_exact_catalog_and_department_counts(self) -> None:
        self.assertTrue(SKILLS_ROOT.is_dir(), f"missing {SKILLS_ROOT}")
        actual = {path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")}
        self.assertEqual(EXPECTED, actual)
        self.assertEqual(46, len(actual))
        for department, expected in EXPECTED_BY_DEPARTMENT.items():
            actual_department = {name for name in actual if name.startswith(f"{department}-")}
            self.assertEqual(expected, actual_department, department)

    def test_frontmatter_sections_and_resource_paths(self) -> None:
        descriptions: dict[str, str] = {}
        for skill_name in sorted(EXPECTED):
            skill_dir = SKILLS_ROOT / skill_name
            skill_file = skill_dir / "SKILL.md"
            fields = parse_frontmatter(skill_file)
            self.assertEqual(skill_name, fields.get("name"), skill_name)
            description = fields.get("description", "")
            self.assertTrue(description.startswith("Use when "), skill_name)
            self.assertGreater(len(description), 35, skill_name)
            self.assertNotIn(description, descriptions, skill_name)
            descriptions[description] = skill_name

            text = skill_file.read_text(encoding="utf-8")
            headings = {line for line in text.splitlines() if line.startswith("## ")}
            self.assertFalse(REQUIRED_HEADINGS - headings, skill_name)
            self.assertNotRegex(text, r"(?i)\b(?:TBD|TODO|FIXME)\b")

            for relative_path in re.findall(
                r"`((?:scripts|references|assets)/[^`\s)]+)`", text
            ):
                self.assertTrue(
                    (skill_dir / relative_path).is_file(),
                    f"{skill_name}: missing {relative_path}",
                )

            agent_config = skill_dir / "agents" / "openai.yaml"
            self.assertTrue(agent_config.is_file(), f"{skill_name}: missing agents/openai.yaml")
            config_text = agent_config.read_text(encoding="utf-8")
            self.assertIn(f"${skill_name}", config_text)

    def test_retired_names_are_not_in_tracked_project_text(self) -> None:
        tracked = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        offenders: list[str] = []
        for relative in tracked:
            if relative.startswith(".worktrees/"):
                continue
            path = ROOT / relative
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            for retired in RETIRED_NAMES:
                if retired in text or retired in relative:
                    offenders.append(f"{relative}: {retired}")
        self.assertEqual([], offenders)

    def test_each_process_stage_names_its_next_handoff(self) -> None:
        for process, chain in PROCESS_CHAINS.items():
            for current, following in zip(chain, chain[1:]):
                text = (SKILLS_ROOT / current / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(
                    f"`{following}`",
                    text,
                    f"{process}: {current} does not hand off to {following}",
                )


if __name__ == "__main__":
    unittest.main()
