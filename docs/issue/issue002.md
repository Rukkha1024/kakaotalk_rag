# Issue 002: Canonical single kakaocli skill for copied Codex setups

**Status**: Done
**Created**: 2026-03-07

## Background

The previous portability work made the repo self-bootstrapping, but the guidance still
spans repo AGENTS files and multiple skill locations. For future Mac setups, the user
wants to copy only one `kakaocli` skill inside `$CODEX_HOME` plus AGENTS files, then
let an AI agent complete the installation from either a GitHub URL or a copied repo.

## Acceptance Criteria

- [x] A single canonical skill exists at `$CODEX_HOME/skills/kakaocli`.
- [x] That skill alone describes the full install and verification workflow for the
      patched repo on macOS.
- [x] Repo guidance points to `$kakaocli` as the canonical skill name.
- [x] The new skill validates cleanly and matches the repo wrapper flow.

## Tasks

- [x] 1. Create the canonical global `kakaocli` skill.
- [x] 2. Make the skill self-contained for clone, copy, install, verification, and
         permission handling.
- [x] 3. Update repo guidance to reference `$kakaocli` as the single skill.
- [x] 4. Validate the skill and commit the change.

## Notes

- Created the canonical global skill at `/Users/alice/.codex/skills/kakaocli/`.
- Mirrored the same self-contained definition into `kakaocli-patched/skills/kakaocli/` for repo tracking.
- Updated repo AGENTS guidance to use `$kakaocli` as the single canonical skill name.
