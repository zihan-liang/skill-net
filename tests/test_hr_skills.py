#!/usr/bin/env python3
"""Structural contract for the HR Codex skill collection."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
EXPECTED_RESOURCES = {
    "hr-job-requirement": set(),
    "hr-jd-generator": {"assets/jd_template.md"},
    "hr-recruitment-publish": set(),
    "hr-resume-screening": {"scripts/screen_resume.py"},
    "hr-interview-scheduling": {"assets/interview_eval.md"},
    "hr-offer-generator": {"scripts/generate_offer.py", "assets/offer_template.md"},
    "hr-onboarding": {"assets/onboarding.md"},
    "hr-employee-database": {
        "scripts/employee_db.py",
        "references/employee_schema.md",
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


def validate() -> list[str]:
    errors: list[str] = []
    actual = (
        {path.name for path in SKILLS.glob("hr-*") if path.is_dir()}
        if SKILLS.exists()
        else set()
    )
    expected = set(EXPECTED_RESOURCES)
    if actual != expected:
        errors.append(
            f"HR skill folders mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )

    for name, resources in EXPECTED_RESOURCES.items():
        folder = SKILLS / name
        skill_file = folder / "SKILL.md"
        agent_file = folder / "agents" / "openai.yaml"
        if not skill_file.is_file():
            errors.append(f"{name}: missing SKILL.md")
            continue
        if not agent_file.is_file():
            errors.append(f"{name}: missing agents/openai.yaml")

        text = skill_file.read_text(encoding="utf-8")
        metadata = parse_frontmatter(text)
        if set(metadata) != {"name", "description"}:
            errors.append(f"{name}: frontmatter must contain only name and description")
        if metadata.get("name") != name:
            errors.append(f"{name}: frontmatter name mismatch")
        if not metadata.get("description", "").startswith("Use when "):
            errors.append(f"{name}: description must start with 'Use when '")
        missing_headings = REQUIRED_HEADINGS - set(text.splitlines())
        if missing_headings:
            errors.append(f"{name}: missing headings {sorted(missing_headings)}")
        if "**中文摘要：**" not in text:
            errors.append(f"{name}: missing Chinese summary")
        if re.search(r"\bTODO\b|\bTBD\b|\[TODO", text):
            errors.append(f"{name}: contains a placeholder")
        if len(text.split()) >= 500:
            errors.append(f"{name}: SKILL.md must remain under 500 words")
        if "Human approval" not in text and "Human confirmation" not in text:
            errors.append(f"{name}: missing human decision boundary")

        for resource in resources:
            resource_file = folder / resource
            if not resource_file.is_file():
                errors.append(f"{name}: missing {resource}")
            if resource not in text:
                errors.append(f"{name}: SKILL.md does not reference {resource}")

        if agent_file.is_file():
            agent_text = agent_file.read_text(encoding="utf-8")
            if f"${name}" not in agent_text:
                errors.append(f"{name}: default prompt must mention ${name}")

    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("HR skill contract failed:")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print(f"Validated {len(EXPECTED_RESOURCES)} HR skill packages.")
