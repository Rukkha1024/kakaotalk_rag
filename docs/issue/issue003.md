# Issue 003: Split public kakaocli from the operator agent repo

**Status**: Done
**Created**: 2026-03-08

## Background

The current repo mixes operator-only agent guidance with the public `kakaocli`
product. The target state is to keep this repo as the operator-facing assistant
workspace while moving the public product into a separate local repository.

## Acceptance Criteria

- [x] The public `kakaocli` snapshot exists as a separate local repo outside this workspace.
- [x] This repo keeps operator-only guidance, docs, and thin wrappers only.
- [x] Product code and product test/config directories are removed from this repo.
- [x] `AGENTS.md` and `.agents/skills/kakaocli/SKILL.md` instruct Codex to use external `PATH` commands and explain what to do if they are missing.

## Tasks

- [x] 1. Export the current public-ready tree into a separate local repo.
- [x] 2. Update operator guidance and root wrappers to call external `PATH` commands.
- [x] 3. Remove embedded public product code from this repo.
- [x] 4. Verify the wrappers and guidance, then commit with a Korean message.

## Notes

The operator repo should remain the source of truth for agent behavior only.
The public repo should be independently managed and should not remain visible as
a branch or embedded directory in this workspace.

## Outcome

Created a separate local public repo at `/Users/alice/Documents/kakaocli-public`
from the public-ready tree, rewired the operator repo to external `PATH`
commands, removed embedded public product code, and deleted the local
`refactor/public-tool-layout` branch from this workspace.
