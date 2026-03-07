# Issue 004: Sync embedding rules documentation with current Live RAG logic

**Status**: Done
**Created**: 2026-03-07

## Background

The workspace has a repository-level `.agents/embedding-rules.md` file that governs
semantic embedding and validation work. After the Live RAG semantic pipeline changed,
that doc no longer matched the actual filter logic, metadata fail-closed behavior,
and semantic config signature rules implemented under `kakaocli-patched/tools/live_rag/`.

## Acceptance Criteria

- [x] `.agents/embedding-rules.md` matches the current semantic candidate filter logic.
- [x] The doc names the local chat metadata and semantic runtime state tables used by
      the builder.
- [x] The doc describes semantic-text construction and config-signature rebuild rules.
- [x] The updated doc does not contradict `kakaocli-patched/README.md`.

## Tasks

- [x] 1. Compare the current rules doc against `semantic_index.py`,
         `build_semantic_index.py`, and `store.py`.
- [x] 2. Update `.agents/embedding-rules.md` in the existing short section style.
- [x] 3. Verify the diff is documentation-only and consistent with repo operator docs.
- [x] 4. Commit the change with the required Korean message.

## Notes

- This work only updates repository guidance; no public API or runtime logic changed.
- Docs verification is based on source cross-checking and diff inspection, not MD5,
  because the semantic pipeline outputs were not modified.
