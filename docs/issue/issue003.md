# Issue 003: Semantic search for Kakao Live RAG and README consolidation

**Status**: Open
**Created**: 2026-03-07

## Background

The patched `kakaocli` repo already has a working local Live RAG pipeline based on
SQLite message storage and lexical retrieval. The next step is to add meaning-based
semantic retrieval using an external embedding API model while keeping the current
local-first ingestion and service flow. At the same time, the patched repo still has a
repo-local `AGENTS.md` file whose content overlaps heavily with `README.md`, even
though the workspace root already provides the authoritative `AGENTS.md`. The
documentation should be consolidated so the patched repo has one clear usage guide.

## Acceptance Criteria

- [ ] `kakaocli-patched/README.md` contains the repo-local operational guidance that
      currently lives in `kakaocli-patched/AGENTS.md`.
- [ ] `kakaocli-patched/AGENTS.md` is removed, and no remaining docs depend on it.
- [ ] The existing Live RAG pipeline supports `lexical`, `semantic`, and `hybrid`
      retrieval modes without breaking current lexical behavior.
- [ ] Semantic retrieval uses an external embedding API model while keeping local
      retrieval state under the repo runtime data directory.
- [ ] The work is validated with runnable commands and MD5 comparison for stable
      output slices where the retrieval pipeline changed.

## Tasks

- [ ] 1. Save bilingual ExecPlan documents for the work under `.agents/exceplan/`.
- [ ] 2. Consolidate `kakaocli-patched/AGENTS.md` into `kakaocli-patched/README.md`.
- [ ] 3. Add semantic indexing and retrieval on top of the existing `tools/live_rag`
         pipeline.
- [ ] 4. Validate the behavior, update issue/workaround records, and prepare the
         required Korean commit.

## Notes

<!-- Record decisions, discoveries, and blockers here as work progresses -->
