# Issue 003: Semantic search for Kakao Live RAG and README consolidation

**Status**: In Progress
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

- [x] `kakaocli-patched/README.md` contains the repo-local operational guidance that
      currently lives in `kakaocli-patched/AGENTS.md`.
- [x] `kakaocli-patched/AGENTS.md` is removed, and no remaining docs depend on it.
- [x] The existing Live RAG pipeline supports `lexical`, `semantic`, and `hybrid`
      retrieval modes without breaking current lexical behavior.
- [x] Semantic retrieval uses an external embedding API model while keeping local
      retrieval state under the repo runtime data directory.
- [ ] The work is validated with runnable commands and MD5 comparison for stable
      output slices where the retrieval pipeline changed.

## Tasks

- [ ] 1. Save bilingual ExecPlan documents for the work under `.agents/exceplan/`.
- [x] 2. Consolidate `kakaocli-patched/AGENTS.md` into `kakaocli-patched/README.md`.
- [x] 3. Add semantic indexing and retrieval on top of the existing `tools/live_rag`
         pipeline.
- [ ] 4. Validate the behavior, update issue/workaround records, and prepare the
         required Korean commit.

## Notes

- Implemented semantic sidecar support in `kakaocli-patched/tools/live_rag/` with
  new `embedding_client.py`, `semantic_index.py`, `build_semantic_index.py`, and
  `validate_semantic.py` entrypoints.
- Extended `app.py`, `query.py`, and `store.py` so `/retrieve` and the CLI expose
  `lexical`, `semantic`, and `hybrid` modes with shared `since_days` filtering and
  semantic rank fusion.
- Updated `requirements-live-rag.txt`, `bin/install-kakaocli`, and `bin/query-kakao`
  so both the conda development path and repo-local `.venv` wrapper path include
  `huggingface_hub` and `numpy`.
- Lexical smoke checks passed after a managed service restart. The wrapper now returns
  the same hit set plus a top-level `"mode": "lexical"` field.
- `validate_semantic.py --use-temp-db` and `build_semantic_index.py` currently fail
  with Hugging Face `403 Forbidden` because the cached login on this Mac does not
  have permission to call inference providers. The scripts now emit structured JSON
  errors instead of raw tracebacks.
- MD5 for `/messages?limit=200` changed between before/after snapshots because the
  sync follower ingested newer live Kakao rows during the implementation window.
  The canonical endpoint still returns the same schema, but a quiet or frozen dataset
  is needed for a stable MD5 proof.
