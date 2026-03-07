#!/usr/bin/env python3
"""Append scenario execution result to tests/scenario_journal.md."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


HEADER = """# Scenario Journal

| timestamp | key | status | note | command |
|---|---|---|---|---|
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update scenario journal")
    parser.add_argument("--repo", type=Path, required=True, help="Repository root path")
    parser.add_argument("--key", type=str, required=True, help="Scenario key")
    parser.add_argument("--status", type=str, required=True, choices=["PASS", "FAIL", "SKIP"])
    parser.add_argument("--note", type=str, default="", help="Short note")
    parser.add_argument("--command", type=str, default="", help="Executed command")
    return parser.parse_args()


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    journal = repo / "tests" / "scenario_journal.md"

    if not repo.exists():
        print(f"[ERROR] repo not found: {repo}")
        return 2

    journal.parent.mkdir(parents=True, exist_ok=True)
    if not journal.exists():
        journal.write_text(HEADER, encoding="utf-8-sig")

    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = (
        f"| {esc(ts)} | {esc(args.key)} | {esc(args.status)} | "
        f"{esc(args.note)} | {esc(args.command)} |\n"
    )

    with journal.open("a", encoding="utf-8-sig") as f:
        f.write(row)

    print(f"[OK] appended: {journal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
