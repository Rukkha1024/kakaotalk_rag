# Issue 001: Portable kakaocli bootstrap for copied repos

**Status**: Done
**Created**: 2026-03-07

## Background

This repo carries a patched `kakaocli` workflow that fixes local KakaoTalk `userId`
discovery, but the current setup still depends on machine-specific absolute paths and
manual tribal knowledge. When the repo is copied or cloned onto another Mac, an AI
agent should be able to install and verify the patched workflow from the repo itself
instead of defaulting to the upstream Homebrew binary.

## Acceptance Criteria

- [x] A repo-local install command exists and resolves paths relative to the copied repo.
- [x] The install flow prepares the required runtime pieces for the patched workflow:
      `sqlcipher`, a repo-local Python runtime, and the local release build.
- [x] Repo instructions and skills prefer the repo-local wrappers over absolute local
      paths or `PATH` `kakaocli`.
- [x] The portable flow is verified from a relocated copy of the repo.

## Tasks

- [x] 1. Add portable install and wrapper scripts at the repo root and inside
         `kakaocli-patched/`.
- [x] 2. Add a reproducible repo-local Python runtime spec for the Live RAG helpers.
- [x] 3. Update README, AGENTS, and skills to route agents through the portable entrypoints.
- [x] 4. Validate the copied-repo workflow from a temporary location.

## Notes

- Added repo-root wrappers: `./install-kakaocli`, `./kakaocli-local`, `./query-kakao`.
- Added repo-local wrappers under `kakaocli-patched/bin/`.
- Replaced conda-based Live RAG bootstrap with a repo-local `.venv`.
- Verified a relocated copy at `/tmp/codex-portable.5B6SXW` with:
  `./install-kakaocli --build-only`, `./kakaocli-local auth`,
  `LIVE_RAG_LAUNCHD_LABEL=com.codex.kakaocli-live-rag-copytest LIVE_RAG_BASE_URL=http://127.0.0.1:8766 ./query-kakao --json --query-text "업데이트"`.
