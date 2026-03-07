#!/usr/bin/env python3
"""Extract scenario keys from tests/test_duplicate_serial_scenarios.py."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PATTERN = re.compile(
    r"""['"](S\d+(?:[_-][A-Za-z0-9_-]+))['"]\s*:\s*Scenario\s*\(""",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract scenario keys")
    parser.add_argument("--repo", type=Path, required=True, help="Repository root path")
    parser.add_argument(
        "--file",
        type=str,
        default="tests/test_duplicate_serial_scenarios.py",
        help="Scenario definition file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    target = repo / args.file

    if not target.exists():
        print(f"[ERROR] file not found: {target}")
        return 2

    text = target.read_text(encoding="utf-8-sig")
    keys = PATTERN.findall(text)

    if not keys:
        print("[WARN] no keys found")
        return 1

    for key in keys:
        print(key)

    print(f"total={len(keys)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
