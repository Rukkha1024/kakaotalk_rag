---
name: scenario-test-lab
description: Build, extend, and execute reusable dummy-data scenario tests under tests/ for duplicate-serial and backup-collision workflows. Use when continuing scenario-based validation (for example S6/S7 style additions), delegating scenario work to multiple agents, and enforcing strict legacy safety (never modify legacy code/files).
---

# Scenario Test Lab

## Enforce Safety First

- Treat every legacy code/file as read-only.
- Never modify production files or existing legacy files.
- Limit write scope to new or explicitly approved test artifacts and records under `tests/`.
- If file ownership is unclear, pause and ask before editing.
- Run `conda run -n module ...` serially only; never run conda commands in parallel.

## Follow This Workflow

1. Inspect current scenario baseline.
2. Define goal-oriented scenarios with explicit pass/fail checks.
3. Delegate scenario design and verification to multiple agents in parallel.
4. Implement new scenarios in test scope only.
5. Execute scenarios serially with `conda run`.
6. Record outcomes in a persistent scenario journal.

## Build Scenario Backlog

Use this minimum matrix and keep extending it.

- `subject_info` duplicate serial, same wear date
- `subject_info` duplicate serial, different wear dates
- backup duplicate with `matching.exhausted_policy=skip`
- backup duplicate with `matching.exhausted_policy=error`
- mixed batch with success + skip + error coexistence

When adding more cases, follow `S<number>_<short_name>` key style and keep old scenarios stable.

## Delegate With Agents

Use parallel agents for design, expectation definition, and review.

- Agent A: draft dummy rows/files and edge-case intent
- Agent B: draft expected statuses/log tokens/final filenames
- Agent C: review scenario consistency and overlap gaps

Then consolidate once and run commands serially.

## Execute Scenarios

Use repository-local runner first (if present), then fall back to direct command.

## Keep Persistent Records

Initialize or append scenario journal entries under `tests/`.

## Use References

- For safety boundaries and mutation policy, read `references/legacy-safety-checklist.md`.
- For scenario catalog patterns and naming, read `references/scenario-catalog.md`.
