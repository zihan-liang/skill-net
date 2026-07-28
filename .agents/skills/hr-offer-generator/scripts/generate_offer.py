#!/usr/bin/env python3
"""Validate approved offer data and render a draft offer template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


PLACEHOLDER = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")


def render_offer(data: dict[str, Any], template: str) -> str:
    if data.get("compensation_approved") is not True:
        raise ValueError("compensation approval is required")
    if data.get("offer_approved") is not True:
        raise ValueError("offer approval is required")

    fields = set(PLACEHOLDER.findall(template))
    missing = sorted(
        field for field in fields if field not in data or data[field] is None or str(data[field]).strip() == ""
    )
    if missing:
        raise ValueError(f"missing template values: {', '.join(missing)}")

    return PLACEHOLDER.sub(lambda match: str(data[match.group(1)]), template)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    data = json.loads(args.data.read_text(encoding="utf-8"))
    template = args.template.read_text(encoding="utf-8")
    args.output.write_text(render_offer(data, template), encoding="utf-8")


if __name__ == "__main__":
    main()
