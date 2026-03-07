# Issue 003: Semantic search for Kakao Live RAG and README consolidation

**Status**: Done
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
- [x] The work is validated with runnable commands and MD5 comparison for stable
      output slices where the retrieval pipeline changed.

## Tasks

- [x] 1. Save bilingual ExecPlan documents for the work under `.agents/exceplan/`.
- [x] 2. Consolidate `kakaocli-patched/AGENTS.md` into `kakaocli-patched/README.md`.
- [x] 3. Add semantic indexing and retrieval on top of the existing `tools/live_rag`
         pipeline.
- [x] 4. Validate the behavior, update issue/workaround records, and prepare the
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
- The semantic builder now checkpoints after each batch and can resume with
  `--mode update --batch-size N --progress`, so a long rebuild no longer has to
  restart from zero after interruption.
- Semantic embedding input now skips non-message/system feed rows and prefixes
  chat/sender/direction metadata before embedding, which improves open-ended
  memory questions against real Kakao history.
- Semantic builds now refresh `chat_metadata` from `kakaocli chats --json`
  before indexing, store that metadata in the local Live RAG database, and
  fail closed if the metadata refresh is incomplete for candidate rows.
- The current embedding rule excludes chats with `member_count > 30` from the
  semantic sidecar. Those chats still remain available to lexical retrieval,
  but they do not contribute semantic chunks or hybrid semantic-sidecar hits.
- The semantic config signature now includes the embedding-rule version plus
  `max_member_count=30`, so rule changes force a rebuild instead of silently
  reusing incompatible incremental state.
- The operator-facing default is now `hybrid`. When the semantic sidecar is
  unavailable, the service falls back to lexical results and includes
  `requested_mode` plus `fallback_reason` in JSON output.
- After rebuilding the sidecar with the new chunk format, both
  `tools/live_rag/query.py --json --query-text "교수님이 나한테 지시하신 게 뭐지?"`
  and `./bin/query-kakao --json --query-text "교수님이 나한테 지시하신 게 뭐지?"`
  returned grounded professor-related hits instead of system feed rows.
- The fixture semantic validator now seeds chat metadata explicitly so the
  new fail-closed embedding rule is covered by automated validation as well.
- MD5 over a quiescent `/messages` slice is now stable. Using
  `chat_id=421983255615844&limit=200`, the before/after snapshots matched with
  hash `9fdd299ebe49192b9a803f2f06ec9abb`.
