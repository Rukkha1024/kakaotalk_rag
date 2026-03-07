# Execution Plan

## Refactoring `kakaotalk_rag` into a stronger Codex CLI evidence layer

### 1. Objective

Refactor the repository so **Codex CLI can answer from two evidence sources at the same time**:

1. the existing stored Kakao history, and
2. live updates coming through `kakaocli`.

The repository should stay a **retrieval and grounding layer**, not turn into a separate answer-generation app. That direction matches the repo itself: `AGENTS.md` routes Kakao requests through `./query-kakao`, the README presents `./bin/query-kakao` as the main evidence-backed entrypoint, and `query.py` identifies itself as the Codex-facing query path.

### 2. Current State

The current foundation is already good for your goal. `./bin/query-kakao` bootstraps the local build and Python runtime, then hands off to `tools/live_rag/query.py`. The retrieval service already supports `lexical`, `semantic`, and `hybrid`, with `hybrid` as the default and lexical fallback when semantic retrieval is unavailable. The semantic sidecar is also reasonably disciplined: canonical `messages` stay separate from `semantic_chunks`, metadata is refreshed before builds, vectors are normalized, and semantic text includes chat and sender context.

The weak points are concentrated in the semantic layer. `embedding_client.py` treats query embeddings and document embeddings as the same operation, while your default model is `Qwen/Qwen3-Embedding-8B`. Hugging Face supports `prompt_name` for feature extraction, and the Qwen model card says retrieval queries should use the query prompt path, while documents do not need that instruction. The code also “batches” at the loop level but still embeds texts one at a time, the best semantic `chunk_text` is found internally but stripped from the returned hit payload, the current semantic validation is only a fixed smoke test, and semantic coverage is capped at chats with `member_count <= 30`.

### 3. Target State

After refactoring, the system should behave like this:

* `./bin/query-kakao` remains the single stable entrypoint for Codex CLI.
* Live mode still exists, because freshness is part of the product value. Today `query.py` ensures the background service is running, the launchd-managed service runs `supervisor.py`, and the supervisor keeps both the webhook server and `run_sync.py` alive; `run_sync.py` launches `kakaocli sync --follow --webhook ...`.
* Codex receives **better evidence objects**, not just raw message text and surrounding context.
* Retrieval quality is measured with benchmark data, not judged by intuition.
* Semantic retrieval is aligned with the actual embedding model you chose.

---

## 4. Workstreams

### Workstream 0 — Freeze a benchmark before changing retrieval behavior

**Why this exists**
Your current semantic validation checks one fixed query against three fixture messages and only verifies that one expected `log_id` appears in the top 3. Your own `llm-evaluation` skill, by contrast, calls out MRR, NDCG, Precision@K, and Recall@K as the right retrieval metrics.

**What to build**
Create a small benchmark corpus of real Kakao-style queries and expected evidence targets. Include:

* name lookup queries
* paraphrase / semantic similarity queries
* date-constrained queries
* speaker-filter queries
* large-group-chat edge cases
* “stored-only” vs “live-recent” cases

**Files**

* `tools/live_rag/validate_semantic.py`
* new benchmark files under `tests/` or `tools/live_rag/eval/`

**Acceptance criteria**

* You can run one command and get MRR, NDCG, Precision@K, Recall@K.
* Every later refactor can be compared against a baseline.
* The old smoke test remains as a quick sanity check.

---

### Workstream 1 — Define a Codex-facing evidence contract

**Why this exists**
Right now the retriever computes strong internal signals, but the final payload is too thin. `store.py` retains the best semantic `chunk_text` while ranking, then `_serialize_hit()` returns only the broader message and neighboring context. That is enough for humans to skim, but not ideal for an answering agent that should ground its response as explicitly as possible.

**What to build**
Add a stable JSON response contract for `query-kakao --json` with fields such as:

* `actual_mode`
* `requested_mode`
* `fallback_reason`
* `retrieval_sources`
* `matched_chunk_text`
* `matched_chunk_id`
* `lexical_score`
* `semantic_score`
* `fusion_score`
* `semantic_config_signature`
* `embedding_model`

**Files**

* `tools/live_rag/store.py`
* `tools/live_rag/app.py`
* `tools/live_rag/query.py`

**Acceptance criteria**

* Codex can see the exact matched chunk, not just the whole message.
* Hybrid hits expose why they ranked where they did.
* The JSON output is stable enough to be used as a machine-consumable interface.

---

### Workstream 2 — Refactor embeddings into model-aware query/document paths

**Why this exists**
The current implementation sends both queries and documents through the same embedding path, without `prompt_name`. Hugging Face documents that `prompt_name` is supported for feature extraction and that omitting it applies no prompt; the Qwen3-Embedding-8B model card specifically distinguishes query usage from document usage and recommends the query prompt path for retrieval queries.

**What to build**
Introduce a lightweight embedding profile layer, for example:

* `QwenProfile`
* `GenericHFProfile`
* later, other model-specific profiles if needed

For Qwen:

* `embed_query()` should use the query-specific prompt path
* `embed_documents()` should use raw document text
* query formatting should be versioned so changes are traceable

**Files**

* `tools/live_rag/embedding_client.py`

**Acceptance criteria**

* Query embeddings and document embeddings are no longer treated as identical.
* The benchmark improves on paraphrase / semantic cases.
* The implementation is extensible when you change embedding models later.

---

### Workstream 3 — Add a true embedding batch path and clean up batch semantics

**Why this exists**
Today, `build_semantic_index.py` chunks inputs in batches, but `embed_documents()` still loops one text at a time. Also, one batching control affects message fetching while another internal constant affects embedding requests, which makes tuning harder than it should be.

**What to build**
Split batching into two explicit layers:

* `message_fetch_batch_size`
* `embedding_request_batch_size`

Then add a provider-aware batch embedding path:

* use array input where the endpoint supports it
* keep the current serial path as fallback

**Files**

* `tools/live_rag/build_semantic_index.py`
* `tools/live_rag/embedding_client.py`

**Acceptance criteria**

* Index build time drops materially.
* Retrieval metrics do not regress.
* Batch knobs have unambiguous names and behavior.

---

### Workstream 4 — Keep RRF as baseline, then add optional reranking

**Why this exists**
The current hybrid path is not broken. Your `hybrid-search-implementation` skill treats Reciprocal Rank Fusion as a good general-purpose baseline and describes reranking as the higher-quality path. So the right move is not “replace hybrid,” but “add an optional higher-precision stage after fusion.”

**What to build**
Keep the current hybrid fusion as default. Then add optional reranking over the top-N candidates, controlled by a flag such as:

* `--rerank off`
* `--rerank on`
* `--rerank auto`

Only make reranking the default if the benchmark proves a clear gain.

**Files**

* `tools/live_rag/app.py`
* new reranker module if needed

**Acceptance criteria**

* Top-k precision improves on difficult semantic queries.
* Latency remains predictable.
* Turning reranking off still preserves current behavior.

---

### Workstream 5 — Improve chunking only where the benchmark says it matters

**Why this exists**
The current semantic chunker uses a fixed `400` character window with `80` character overlap. For short chat messages, that is usually fine. For long notices, pasted schedules, or dense multi-sentence updates, it is a weaker strategy than message-aware or sentence-aware chunking.

**What to build**
Do not over-engineer this globally. Keep the current simple behavior for short messages, and add improved chunking only for long texts, for example:

* line-aware chunking for notice-style content
* sentence-aware chunking for long prose
* current windowing as fallback

**Files**

* `tools/live_rag/semantic_index.py`

**Acceptance criteria**

* Long-message recall improves in the benchmark.
* Short-message behavior stays stable.
* Chunking logic remains simple enough to maintain.

---

### Workstream 6 — Turn semantic coverage into a configurable policy

**Why this exists**
The repo currently excludes chats above `member_count <= 30` from semantic indexing. That is a policy choice, not a fundamental technical limit. It may be sensible as a default, but it will hurt Codex if your important evidence lives in large rooms.

**What to build**
Keep the current default cap, but add:

* chat allowlist
* chat denylist
* optional per-chat override for semantic eligibility

**Files**

* `tools/live_rag/build_semantic_index.py`
* `tools/live_rag/store.py`
* optional config file such as `semantic_policy.yaml`

**Acceptance criteria**

* You can opt important large chats into semantic indexing.
* Index growth stays controlled.
* Coverage decisions become explicit instead of hidden in code.

---

### Workstream 7 — Keep live sync, but make service mode explicit

**Why this exists**
The repo currently assumes that querying should also ensure the live service is running. For your goal, that is reasonable. But it is still better engineering to make that behavior explicit and selectable. It also helps reconcile the current design with the stricter `kakaocli` skill guidance, which says `sync --follow` should be used only when explicitly needed.

**What to build**
Add a service mode switch such as:

* `follow`
* `server-only`
* `off`

Keep `follow` as the default for Codex CLI if freshness is your priority.

**Files**

* `tools/live_rag/service_manager.py`
* `tools/live_rag/supervisor.py`
* `tools/live_rag/run_sync.py`
* `tools/live_rag/query.py`

**Acceptance criteria**

* Current behavior still works by default.
* Offline benchmarking becomes easier.
* Service behavior is intentional rather than implicit.

---

## 5. Sequencing

Recommended order:

1. **Workstream 0 — Benchmark**
2. **Workstream 1 — Codex evidence contract**
3. **Workstream 2 — Embedding adapter**
4. **Workstream 3 — True batching**
5. **Workstream 4 — Optional reranking**
6. **Workstream 5 — Long-message chunking**
7. **Workstream 6 — Coverage policy**
8. **Workstream 7 — Service-mode cleanup**

This order puts **measurement first**, then **evidence visibility**, then **semantic correctness**, then **performance**, then **precision tuning**, then **policy cleanup**. That sequencing fits the actual weaknesses visible in the current code and the repo’s own skill criteria.

## 6. Non-goals

Do **not** spend time turning this repository into a monolithic assistant that also generates the final answer. The repo already positions itself as the Codex-facing retrieval path, and your own stated goal is to let Codex CLI answer from stored and live Kakao evidence. The right refactor is to make retrieval more accurate, more measurable, and easier for Codex to consume.

## 7. Exit Criteria

This refactor is done when all of the following are true:

* Codex receives stable, explicit evidence objects with matched chunks and retrieval provenance.
* Semantic query behavior is aligned with the actual embedding model.
* Retrieval quality is measured with benchmark metrics, not guessed.
* Live freshness remains available.
* Important large chats can be included deliberately when needed.
* `./bin/query-kakao` remains the main operator entrypoint.

The next clean step is to turn this into a **file-by-file implementation checklist** with exact edits per module.

[1]: https://lobehub.com/skills/kevinslin-llm-dev.exec-plan?utm_source=chatgpt.com "dev.exec-plan | Skills Marketplace"

## 8. Progress

- [x] (2026-03-07 12:24Z) Created issue tracking in `docs/issue/issue001.md` and `docs/dev/issue/issue001.ko.md`.
- [x] (2026-03-07 12:24Z) Added deterministic benchmark fixtures, snapshot generation, and smoke validation under `kakaocli-patched/tools/live_rag/validate_semantic.py`, `kakaocli-patched/tools/live_rag/eval_support.py`, and `kakaocli-patched/tools/live_rag/eval/`.
- [x] (2026-03-07 12:24Z) Replaced the hit serialization contract so retrieval results include `actual_mode`, `requested_mode`, matched chunk provenance, source attribution, and per-stage scores.
- [x] (2026-03-07 12:24Z) Refactored embeddings into model-aware query/document paths and added provider-aware batch attempts with serial fallback.
- [x] (2026-03-07 12:24Z) Added line-aware and sentence-aware long-message chunking and explicit semantic policy loading from `configs/live_rag_semantic_policy.yaml`.
- [x] (2026-03-07 12:24Z) Added explicit service mode wiring across query/service/supervisor paths.
- [x] (2026-03-07 12:24Z) Added regression tests and locked the deterministic reference snapshot MD5.

## 9. Surprises & Discoveries

- Observation: `huggingface_hub.InferenceClient.feature_extraction` exposes a public single-string API even though the provider helper can prepare requests with `inputs: Any`.
  Evidence: local signature inspection showed `feature_extraction(self, text: str, ..., prompt_name: Optional[str] = None, ...)`.
- Observation: semantic chunk IDs change when the semantic policy signature changes because the policy feeds the semantic config signature.
  Evidence: the first regression snapshot mismatch disappeared once the fixture policy signature matched the validation policy signature.
- Observation: `unittest discover` did not recurse into the new `tests/live_rag/` tree until `__init__.py` files were added.
  Evidence: initial discovery ran `0 tests`; after adding package markers it ran `4 tests`.

## 10. Decision Log

- Decision: Keep the human-readable text rendering close to the prior CLI output while expanding the JSON response contract.
  Rationale: the user required baseline-visible behavior to stay stable while still adopting the stronger machine-readable evidence layer.
  Date/Author: 2026-03-07 / Codex
- Decision: Use a deterministic local embedding client for benchmark and regression validation.
  Rationale: this keeps smoke, benchmark, snapshot, and MD5 comparison reproducible without depending on external inference availability.
  Date/Author: 2026-03-07 / Codex
- Decision: Treat legacy defaults as replaced, but keep limited non-default safety controls such as rerank mode and service mode for validation and recovery.
  Rationale: the approved direction was hard replacement of the production default path, not removal of every operational control.
  Date/Author: 2026-03-07 / Codex
- Decision: Record the real implementation root as `kakaocli-patched/tools/live_rag/` even though the original plan text used `tools/live_rag/`.
  Rationale: the checked-in code lives under the patched subrepo and the implementation had to follow the real paths to stay executable.
  Date/Author: 2026-03-07 / Codex

## 11. Outcomes & Retrospective

The plan is implemented in the working tree. The retrieval layer now returns richer evidence objects, deterministic validation produces benchmark metrics and a locked snapshot MD5, semantic policy moved into YAML, embedding/query handling is model-aware, and long-message chunking no longer relies only on a fixed window. The main remaining risk is environment-specific live launchd behavior, which cannot be fully proven from fixture validation alone.

Revision note: appended implementation progress, discoveries, decisions, and outcomes so this ExecPlan remains a usable living document during and after execution.
