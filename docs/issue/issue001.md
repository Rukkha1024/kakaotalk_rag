# Issue 001: Strengthen the Codex-facing Kakao Live RAG evidence layer

**Status**: Done
**Created**: 2026-03-07

## Background

The current Kakao Live RAG path works, but the evidence contract is too thin,
semantic evaluation is not benchmarked, embeddings treat queries and documents
the same way, batching is only partial, and semantic coverage is hidden in code.
This work applies the approved ExecPlan so Codex can consume stronger evidence
objects while the observable retrieval behavior stays stable for existing flows.

## Acceptance Criteria

- [x] A deterministic benchmark command reports MRR, NDCG, Precision@K, and Recall@K.
- [x] `./query-kakao --json` returns a stable evidence contract with matched chunk provenance.
- [x] Query and document embeddings use distinct model-aware paths.
- [x] Semantic index building uses real embedding batches and explicit batch controls.
- [x] Chunking, semantic coverage, and service mode are explicit policies, not hidden defaults.
- [x] Legacy default production branches replaced by the new implementation still preserve baseline outputs where compatibility is expected.

## Tasks

- [x] 1. Capture a deterministic fixture baseline and add benchmark/reference outputs.
- [x] 2. Replace the evidence contract and retrieval payload shaping.
- [x] 3. Refactor embeddings, batching, chunking, and semantic policy handling.
- [x] 4. Make the new service behavior explicit and default-on.
- [x] 5. Validate with fixture benchmarks, MD5 comparison, and repository test commands.
- [x] 6. Update the ExecPlan progress log and finalize with a Korean commit message.

## Notes

The approved direction is hard replacement of legacy defaults. Recovery and
comparison paths may remain only as non-default validation or operator safety
mechanisms if they do not reintroduce the legacy production path.

Validation summary:
- `conda run -n module python -m unittest discover -s tests -p 'test_*.py'` -> `4` tests passed.
- `conda run -n module python kakaocli-patched/tools/live_rag/validate_semantic.py --use-temp-db --backend deterministic --validation all` -> snapshot MD5 `fb7059a13b81bfe358c51657ba3aadf0`, `matches_reference=true`.
