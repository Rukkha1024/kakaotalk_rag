#!/usr/bin/env python3
"""Run duplicate-serial scenarios sequentially via conda."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scenario tests serially")
    parser.add_argument("--repo", type=Path, required=True, help="Repository root path")
    parser.add_argument(
        "--runner",
        type=str,
        default="tests/test_duplicate_serial_scenarios.py",
        help="Scenario runner python file path (repo-relative)",
    )
    parser.add_argument("--keys", type=str, default="", help="Comma-separated scenario keys")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    return parser.parse_args()


def run_command(repo: Path, args: List[str]) -> subprocess.CompletedProcess:
    cmd = ["conda", "run", "-n", "module", "python", *args]
    return subprocess.run(cmd, cwd=str(repo), text=True, capture_output=True)


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    runner = args.runner

    if not repo.exists():
        print(f"[ERROR] repo not found: {repo}")
        return 2

    keys = [k.strip() for k in args.keys.split(",") if k.strip()]

    plan: List[List[str]] = []
    if args.all or not keys:
        plan.append([runner, "--all"])
    else:
        for key in keys:
            plan.append([runner, "--scenario", key])

    total = len(plan)
    passed = 0

    for idx, run_args in enumerate(plan, start=1):
        print(f"\n[{idx}/{total}] Running: {' '.join(run_args)}")
        result = run_command(repo, run_args)
        print(result.stdout)
        if result.stderr:
            print("[stderr]")
            print(result.stderr)

        if result.returncode == 0:
            passed += 1
            print("[PASS]")
        else:
            print(f"[FAIL] exit={result.returncode}")

    failed = total - passed
    print("\n" + "=" * 60)
    print(f"Summary: PASS {passed} / FAIL {failed} (total {total})")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
