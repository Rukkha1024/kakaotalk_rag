"""Create timestamped progress markdown notes.

Use local time for `YYMMDD-HHMM-subject.md`,
write the standard section template,
and print the created file path.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


TEMPLATE = """# {title}

## Goal

- 

## What Was The Problem

- 

## What Was Done

- 

## Validation

- 

## Future Improvements

- 
"""


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        raise ValueError("Subject must contain at least one ASCII letter or digit.")
    return normalized


def titleize(subject: str) -> str:
    return " ".join(part.capitalize() for part in subject.split("-"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a timestamped progress markdown note.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--title")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    subject = slugify(args.subject)
    timestamp = datetime.now().astimezone().strftime("%y%m%d-%H%M")
    filename = f"{timestamp}-{subject}.md"
    path = output_dir / filename

    if path.exists() and not args.overwrite:
        raise SystemExit(f"Refusing to overwrite existing file: {path}")

    title = args.title or titleize(subject)
    path.write_text(TEMPLATE.format(title=title), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
