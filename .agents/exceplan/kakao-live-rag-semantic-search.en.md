# Extend Kakao Live RAG with External-Embedding Semantic Search

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. This document must be maintained in accordance with `.agents/PLANS.md` from the repository root.

## Purpose / Big Picture

After this change, the existing Kakao Live RAG flow will still ingest messages locally through `kakaocli`, but retrieval will no longer depend only on exact keyword overlap. A user will be able to ask for a meaning-based match such as “the message where someone postponed the meeting” even when the wording in the chat does not exactly match the query. The visible proof will be that the existing `tools/live_rag/query.py` command can return useful hits in `semantic` or `hybrid` mode while the current lexical mode still works. In the same change, the repo documentation will be simplified so `kakaocli-patched/README.md` becomes the single repo-local usage guide and the repo-local `AGENTS.md` file is retired.

## Progress

- [x] (2026-03-07 05:54Z) Confirmed that the current retrieval path is lexical SQLite FTS plus `LIKE` fallback in `kakaocli-patched/tools/live_rag/store.py`.
- [x] (2026-03-07 05:54Z) Confirmed that the existing service shape is `backfill.py` and `run_sync.py` for ingestion, `app.py` for HTTP endpoints, and `query.py` for the Codex-facing CLI.
- [x] (2026-03-07 05:54Z) Confirmed that `kakaocli-patched/AGENTS.md` duplicates large parts of `kakaocli-patched/README.md`, and its remaining unique material belongs in the README instead of a second agent-rules file.
- [x] (2026-03-07 06:03Z) Saved bilingual tracking issue documents as `docs/issue/issue003.md` and `docs/dev/issue/issue003.ko.md`.
- [x] (2026-03-07 06:03Z) Saved this English ExecPlan and the Korean counterpart under `.agents/exceplan/`.
- [x] (2026-03-07 06:24Z) Revised both ExecPlan files after review so the validation path is reproducible, the AGENTS retirement check only searches `kakaocli-patched/`, and bookkeeping points to concrete issue/progress paths that exist in this repo.
- [x] (2026-03-07 07:25Z) Merged the repo-local `kakaocli-patched/AGENTS.md` content into `kakaocli-patched/README.md`, removed README links that required a separate repo-local AGENTS file, and deleted `kakaocli-patched/AGENTS.md`.
- [x] (2026-03-07 07:25Z) Added a semantic indexing path that reads from the existing `messages` table, chunks text windows, calls the Hugging Face embedding API through `huggingface_hub`, and stores local semantic metadata in the Live RAG SQLite database under `.data/`.
- [x] (2026-03-07 07:25Z) Exposed `lexical`, `semantic`, and `hybrid` retrieval through the existing service and CLI without removing the lexical fallback path.
- [x] (2026-03-07) Verified the runtime path still works after the semantic changes: `conda run -n module python -m compileall tools/live_rag`, `./bin/install-kakaocli --build-only`, service restart, and `./bin/query-kakao --json --mode lexical --query-text "업데이트"` all succeeded.
- [x] (2026-03-07) Verified deterministic semantic validation with a fixture-backed temp database after supplying a valid Hugging Face token; `tools/live_rag/validate_semantic.py --use-temp-db` returned the expected semantic hit set.
- [x] (2026-03-07) Fixed the Qwen embedding response parser so `Qwen/Qwen3-Embedding-8B` results shaped like `(1, 4096)` are accepted instead of treated as an unsupported payload.
- [x] (2026-03-07) Confirmed a limited real-data semantic rebuild succeeds; `tools/live_rag/build_semantic_index.py --mode rebuild --limit 20` completed and persisted sidecar state in `.data/live_rag.sqlite3`.
- [x] (2026-03-07) Ran a targeted lab-chat semantic probe by embedding a recent research-lab subset and using the question “최근 연구실 사람들 간의 대화 주제가 뭐지?” to retrieve meaning-based hits from the recent conversations.
- [x] (2026-03-07) Added batch checkpointing and progress-visible semantic builds; `build_semantic_index.py --mode update --limit 20 --batch-size 20 --progress` resumed from the rebuild checkpoint and advanced `semantic_last_indexed_log_id` without clearing prior chunks.
- [x] (2026-03-07) Filtered semantic indexing down to real text messages, prefixed chat/sender/direction metadata before embedding, and verified that the professor-instruction question now returns grounded professor-chat hits in `semantic`/default `hybrid` mode.
- [x] (2026-03-07) Set the operator-facing default retrieval behavior to `hybrid` with lexical fallback when semantic state is unavailable, and documented the fallback metadata returned in JSON responses.
- [x] (2026-03-07) Reran `/messages` MD5 on a quiescent chat slice (`chat_id=421983255615844&limit=200`) and confirmed the before/after hashes matched as `9fdd299ebe49192b9a803f2f06ec9abb`.

## Surprises & Discoveries

- Observation: The repository already has a durable local service with automatic restart and query routing, so the right place to add semantics is the current `tools/live_rag` path, not a parallel mini-RAG.
  Evidence: `kakaocli-patched/tools/live_rag/query.py` already ensures the service is running before it calls `/retrieve`.

- Observation: The current canonical source of truth is the local SQLite database, not ad hoc chat files.
  Evidence: `kakaocli-patched/tools/live_rag/store.py` defines `messages`, FTS state, and ingestion checkpoint state in one database.

- Observation: The Python dependency surface is currently very small, so adding native-heavy or framework-heavy layers would be out of character for this repo.
  Evidence: `kakaocli-patched/requirements-live-rag.txt` currently contains only `fastapi` and `uvicorn`.

- Observation: `kakaocli-patched/README.md` already contains most operator documentation, while `kakaocli-patched/AGENTS.md` mainly duplicates it plus a few repo-local operational details.
  Evidence: the README currently links to `AGENTS.md` in several places instead of carrying those instructions directly.

- Observation: the operator-facing wrapper path does not run the conda environment directly; `kakaocli-patched/bin/query-kakao` uses the repo-local `.venv` and bootstraps it through `./bin/install-kakaocli`.
  Evidence: `kakaocli-patched/bin/query-kakao` exports `LIVE_RAG_PYTHON` from `.venv/bin/python`, and `kakaocli-patched/bin/install-kakaocli` rebuilds that environment from `requirements-live-rag.txt`.

- Observation: `huggingface_hub==1.1.0` exposes `InferenceClient.feature_extraction` as a single-text call, not a list-of-texts batch API.
  Evidence: local signature inspection showed `feature_extraction(self, text: str, ..., model: Optional[str] = None) -> np.ndarray`, so document embedding had to loop one text at a time.

- Observation: the current cached Hugging Face login on this Mac exists but lacks permission to call inference providers for embeddings.
  Evidence: both `tools/live_rag/validate_semantic.py --use-temp-db` and `tools/live_rag/build_semantic_index.py` returned `403 Forbidden` from `router.huggingface.co`, even when `--embedding-provider hf-inference` was specified.

- Observation: global `/messages?limit=200` MD5 was unstable during implementation because live ingestion continued, but a quiescent chat-scoped slice was stable.
  Evidence: the original global export drifted as newest and oldest `log_id` values changed, while `chat_id=421983255615844&limit=200` produced matching before/after hashes of `9fdd299ebe49192b9a803f2f06ec9abb`.

- Observation: forcing `--embedding-provider hf-inference` was not the stable way to reach `Qwen/Qwen3-Embedding-8B` from this environment.
  Evidence: after valid credentials were supplied, explicit `hf-inference` calls returned `404`, while the default routed provider returned embeddings successfully.

- Observation: the successful Qwen embedding payload arrived as a two-dimensional array for a single text, not a flat vector.
  Evidence: direct inspection of `InferenceClient.feature_extraction(..., model="Qwen/Qwen3-Embedding-8B")` returned a payload shaped like `(1, 4096)`, which required a parser fix before fixture validation passed.

- Observation: a small chat-scoped semantic probe was useful before the full rebuild finished.
  Evidence: indexing only recent lab-related chats produced semantically relevant hits for the “recent lab conversation topics” question, while a tiny global rebuild over the oldest rows did not.

- Observation: system/feed rows were strong semantic noise sources for open-ended memory questions.
  Evidence: before filtering, the professor-instruction query ranked `feedType` JSON rows and photo placeholders near the top; after restricting semantic indexing to real text messages and embedding metadata, the same question returned professor-related chats.

## Decision Log

- Decision: Extend the existing `kakaocli-patched/tools/live_rag` pipeline instead of adding a new general transcript-import feature in the first pass.
  Rationale: The repo already normalizes Kakao messages into a durable SQLite store and has a working service, so the safest change is to add semantics on top of that source of truth.
  Date/Author: 2026-03-07 / Codex

- Decision: Keep the external embedding API concept, but keep storage and retrieval local.
  Rationale: The user explicitly wants external embeddings for semantic search, but the repo style is local-first, so vectors, metadata, and ranking should remain on disk inside the repo runtime state.
  Date/Author: 2026-03-07 / Codex

- Decision: Do not require FAISS in the first implementation pass unless profiling proves brute-force local vector scoring is too slow.
  Rationale: This repo is already SQLite-based, has modest dependencies, and a first pass using local stored vectors plus NumPy cosine scoring is simpler, easier to debug, and more aligned with the existing style. A later migration to FAISS remains possible behind the same retrieval interface.
  Date/Author: 2026-03-07 / Codex

- Decision: Keep lexical retrieval and add semantic and hybrid modes rather than replacing the current search path.
  Rationale: This is a feature addition, not a bug fix. Retaining lexical retrieval protects exact-name and exact-phrase lookups while allowing semantic recall for paraphrased questions.
  Date/Author: 2026-03-07 / Codex

- Decision: Retire `kakaocli-patched/AGENTS.md` and merge its repo-local operational content into `kakaocli-patched/README.md`.
  Rationale: The root repo already has the authoritative `AGENTS.md` rules file. Keeping a second repo-local `AGENTS.md` inside `kakaocli-patched/` is structurally confusing, duplicates existing README material, and makes operators chase links between two user-facing docs.
  Date/Author: 2026-03-07 / Codex

- Decision: Make the embedding model and provider configurable, with `Qwen/Qwen3-Embedding-8B` as the default target model but not a hard-coded provider.
  Rationale: Hugging Face routing and provider availability can vary by account and model deployment, so the code should accept `HF_TOKEN` or prior `hf auth login`, and optionally a provider name, without baking in one brittle provider string.
  Date/Author: 2026-03-07 / Codex

- Decision: Make semantic acceptance depend on a deterministic fixture-backed validation script, then use the real Kakao database only for smoke checks and MD5 stability checks.
  Rationale: Real Kakao history differs across machines, so a fixed live query cannot be the primary proof of semantic behavior. A temporary fixture database gives reproducible evidence, while the real database still proves the wrapper and ingestion path remain usable.
  Date/Author: 2026-03-07 / Codex

- Decision: Delay `rebuild` sidecar deletion until after embedding calls succeed, and emit JSON error payloads from the semantic build/validation entrypoints.
  Rationale: If Hugging Face authentication fails, the existing semantic state should remain intact, and operators need machine-readable failure output instead of raw tracebacks.
  Date/Author: 2026-03-07 / Codex

- Decision: Prefer the default Hugging Face routed provider path for `Qwen/Qwen3-Embedding-8B` instead of forcing `hf-inference`.
  Rationale: In this environment the explicit `hf-inference` route returned `404`, while the default provider routing returned valid embeddings once token permission and billing were in place.
  Date/Author: 2026-03-07 / Codex

- Decision: Use targeted chat-scoped semantic probes as an interim validation technique while the full real-data rebuild remains slow or operationally expensive.
  Rationale: The fixture database proves semantic correctness, and a focused recent-chat probe proves user-facing value sooner than waiting on a long global rebuild.
  Date/Author: 2026-03-07 / Codex

- Decision: Make `hybrid` the operator-facing default and fall back to lexical only when semantic state is unavailable.
  Rationale: Real query evidence showed that open-ended memory prompts benefit from semantic recall, while lexical fallback preserves safe behavior before the sidecar exists or when embedding calls fail.
  Date/Author: 2026-03-07 / Codex

## Outcomes & Retrospective

Implementation is now in place and the semantic path is no longer just theoretical. The patched repo has one operator-facing guide in `kakaocli-patched/README.md`, the duplicate repo-local `AGENTS.md` file is gone, and the Live RAG code path now includes semantic-sidecar build/update scripts plus `lexical`, `semantic`, and `hybrid` retrieval modes in the service and CLI. Lexical behavior still works through the managed wrapper after a service restart. Fixture-backed semantic validation passes with `Qwen/Qwen3-Embedding-8B`, the parser accepts the routed provider's `(1, 4096)` response shape, and the builder now checkpoints per batch so long rebuilds can resume through `--mode update` instead of restarting from zero. After filtering non-message rows and embedding chat/sender/direction metadata, the professor-instruction query returns grounded professor-chat hits in both the direct CLI and `./bin/query-kakao`, so the operator-facing default is now `hybrid` with explicit lexical fallback metadata. The MD5 check is also closed on a quiescent `/messages` slice, where the before/after hashes matched exactly. The remaining optional follow-up is purely operational: let the resumable rebuild continue to full coverage when convenient.

## Context and Orientation

The relevant implementation lives under `kakaocli-patched/tools/live_rag`. The file `store.py` is the current local database layer. It stores normalized Kakao messages, an FTS index for keyword search, and the checkpoint used to resume live sync. The file `app.py` exposes `/health`, `/messages`, `/kakao`, and `/retrieve`. The file `query.py` is the command-line entrypoint that ensures the background service is running and then submits a retrieval request. The file `backfill.py` imports older messages from `kakaocli`, while `run_sync.py` keeps live ingestion moving forward.

The relevant human-facing docs currently live in two places inside the patched repo: `kakaocli-patched/README.md` and `kakaocli-patched/AGENTS.md`. The root repository already has its own top-level `AGENTS.md`, which is the actual rules file for work in this workspace. Because of that, the patched repo’s `AGENTS.md` should be treated as an operational document, not as a second authority on agent rules. In this plan, that operational content will be merged into `README.md`, and the repo-local `AGENTS.md` file will be deleted.

In this plan, “semantic retrieval” means finding text by similar meaning rather than by exact shared words. An “embedding” is a list of numbers produced by a model so that semantically similar texts land near each other. A “chunk” is a smaller search unit derived from one message or a short local message window so that long or noisy chat history does not become one giant vector. A “hybrid retrieval” result is a combined ranking that uses both exact keyword evidence and semantic similarity.

The first-pass scope deliberately avoids adding generic `.txt`, `.md`, `.json`, and `.jsonl` transcript import. This repo already has a cleaner message source: the Kakao message rows in `live_rag.sqlite3`. If external transcript import is ever needed, it should be a separate issue after this change proves useful.

The user-facing query wrapper is `/Users/alice/Documents/codex/query-kakao`, which delegates to `kakaocli-patched/bin/query-kakao`. That wrapper runs the patched repo’s `.venv`, not the `module` conda environment directly, and it calls `./bin/install-kakaocli --build-only` when the local runtime is missing or stale. Because of that, dependency edits in `kakaocli-patched/requirements-live-rag.txt` must be validated through both direct `conda run -n module python ...` development commands and the wrapper path that operators actually use.

## Plan of Work

The semantic path, README consolidation, and retrieval-mode wiring described earlier in this document already exist in the working tree. The next session is therefore not a greenfield implementation pass. Its job is to verify that the existing semantic path remains healthy, extend only the parts that are still operationally weak, and record the final operator-facing behavior. The first milestone is to turn the semantic path from “proven on fixtures and subsets” into “useful on the real database.” Start by confirming the current fixture validation still passes and inspecting the current semantic-sidecar stats in `.data/live_rag.sqlite3`. Then attempt a full rebuild against the real message store with the current Qwen configuration. If the rebuild completes in a reasonable time, record the resulting semantic counts and move directly to operator-facing query validation. If it does not, pause and make `build_semantic_index.py` more operationally usable by adding resumable batching and visible progress so a long rebuild can be resumed instead of restarted blindly.

The second milestone is to decide the operator-facing retrieval default. The code already supports `lexical`, `semantic`, and `hybrid`, but the next session needs an explicit answer to what `query-kakao` should do for open-ended memory questions such as “교수님이 나한테 지시하신 게 뭐지?” There are only three sane choices: keep lexical as the default and require an explicit mode switch, change the default to hybrid, or add a small fallback rule that uses hybrid/semantic for broad memory questions while preserving lexical for exact phrase lookups. The decision should be made with real query evidence, not by taste.

The third milestone is user-facing semantic validation on real chat history. After a meaningful sidecar exists, run both `tools/live_rag/query.py` and `./bin/query-kakao` in `semantic` and `hybrid` modes with a question that resembles how the operator will actually ask. The key smoke test is whether a question like “교수님이 나한테 지시하신 게 뭐지?” returns hits grounded in the intended professor-related chats rather than random early messages. If the results are weak, inspect whether the failure is due to insufficient index coverage, chunking strategy, recency filtering, or ranking combination.

The fourth milestone is cleanup and proof. Rerun the `/messages` MD5 comparison only after choosing a frozen or quiescent slice so ingestion drift does not invalidate the comparison. Then update `docs/issue/issue003.md`, `docs/dev/issue/issue003.ko.md`, and this ExecPlan pair with the final operator behavior, semantic build status, and any reusable rebuild workaround that future sessions should know.

## Concrete Steps

All commands below assume the working directory is `/Users/alice/Documents/codex/kakaocli-patched` unless a command explicitly says otherwise.

1. Confirm the semantic baseline still works before touching more code.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module python tools/live_rag/validate_semantic.py --use-temp-db

    Expected result:
      The fixture-backed semantic validation returns `{"status":"ok",...}` and proves the current token, model, and parser path are still healthy.

2. Inspect the current semantic sidecar state so the next session starts from facts instead of assumptions.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module python - <<'PY'
    from tools.live_rag.store import LiveRAGStore
    store = LiveRAGStore()
    print(store.semantic_stats())
    PY

    Expected result:
      The command prints the current semantic chunk count, message count, and configuration signature already stored in `.data/live_rag.sqlite3`.

3. Attempt a meaningful real-data semantic rebuild with the current Qwen configuration.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module python tools/live_rag/build_semantic_index.py --mode rebuild

    Expected result:
      Either the command completes with JSON success and a large embedded chunk count, or it proves the remaining operational problem is rebuild duration rather than embedding correctness.

4. If the full rebuild is too slow or too opaque, improve the builder instead of repeatedly restarting it blindly.

    Goal for the edit:
      Add resumable batching and visible progress output to `tools/live_rag/build_semantic_index.py`, then rerun the rebuild until a useful full-database sidecar exists.

5. Restart the managed service and query through both direct and wrapper entrypoints.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module python tools/live_rag/service_manager.py restart
    conda run -n module python tools/live_rag/query.py --mode semantic --json --query-text "교수님이 나한테 지시하신 게 뭐지?"
    conda run -n module python tools/live_rag/query.py --mode hybrid --json --query-text "교수님이 나한테 지시하신 게 뭐지?"
    ./bin/query-kakao --json --mode semantic --query-text "교수님이 나한테 지시하신 게 뭐지?"
    ./bin/query-kakao --json --mode hybrid --query-text "교수님이 나한테 지시하신 게 뭐지?"

    Expected result:
      At least one operator-facing mode returns hits grounded in the intended professor-related chats instead of arbitrary old messages.

6. Decide the default operator behavior only after examining the real query evidence.

    Decision to record:
      Keep `lexical` as default, switch default to `hybrid`, or introduce a narrow fallback rule for open-ended memory questions.

7. Rerun MD5 on a frozen or quiescent message slice.

    cd /Users/alice/Documents/codex/kakaocli-patched
    curl -s http://127.0.0.1:8765/messages?limit=200 > /tmp/live_rag_messages_frozen_before.json
    md5 /tmp/live_rag_messages_frozen_before.json
    # perform the semantic-sidecar work without changing canonical messages
    curl -s http://127.0.0.1:8765/messages?limit=200 > /tmp/live_rag_messages_frozen_after.json
    md5 /tmp/live_rag_messages_frozen_after.json

    Expected result:
      The hashes match on a truly stable slice, or any mismatch is explained as ingestion drift rather than a semantic-sidecar regression.

8. Update the issue docs and both ExecPlans with the final next-session outcome.

    cd /Users/alice/Documents/codex
    sed -n '1,160p' docs/issue/issue003.md
    sed -n '1,160p' docs/dev/issue/issue003.ko.md

    Expected result:
      The issue docs and this ExecPlan pair record whether the full semantic rebuild finished, what default retrieval behavior was chosen, and how the operator-facing professor-question test behaved.

## Validation and Acceptance

Acceptance is behavioral. The change is accepted only if all of the following are true.

- The existing lexical query path still returns hits for an exact keyword query through `tools/live_rag/query.py`.
- `./bin/query-kakao --json --mode lexical --query-text "업데이트"` still works, proving the repo-local wrapper path remains healthy after the semantic changes.
- `tools/live_rag/validate_semantic.py --use-temp-db` still returns the expected fixture hit for a paraphrased query in `semantic` mode with `Qwen/Qwen3-Embedding-8B`.
- A meaningful real-data semantic sidecar exists for the operator's current Kakao history, either via one successful full rebuild or via a resumable rebuild path that can complete without restarting from zero.
- `semantic` and/or `hybrid` mode returns hits for the question “교수님이 나한테 지시하신 게 뭐지?” that are grounded in the intended professor-related chats instead of arbitrary old messages.
- The team records an explicit decision about the default operator-facing retrieval behavior rather than leaving `query-kakao` mode selection ambiguous.
- Restarting the service does not lose the semantic sidecar state because it is persisted under `.data/`.
- Incremental index refresh only processes newly ingested message rows, or clearly and safely performs a rebuild when configuration changes.
- The `/messages` endpoint output remains stable before and after the semantic-sidecar work, as shown by MD5 comparison on a frozen or quiescent reference slice.
- `kakaocli-patched/README.md` alone explains installation, credentials, lifecycle, Live RAG routing, and local agent/operator caveats without sending the reader to a second repo-local `AGENTS.md`.
- There are no remaining references that require `kakaocli-patched/AGENTS.md`.
- The docs explain how to authenticate with Hugging Face using either `HF_TOKEN` or prior `hf auth login`.
- The retrieval request schema and CLI expose the same explicit recency control, and that control is applied consistently in lexical, semantic, and hybrid modes.
- The implementation can be run with `conda run -n module python ...` and does not require a new vector database or a new UI.

## Idempotence and Recovery

The plan must be safe to run multiple times. Re-running `build_semantic_index.py --mode rebuild` should replace only semantic sidecar data and must never delete canonical Kakao messages. Re-running `--mode update` should skip already indexed message rows based on stored checkpoint state or stored chunk signatures. If the embedding model name, provider, chunking rules, or query template changes, the plan should force a clean semantic rebuild and leave a clear message explaining why. If Hugging Face authentication fails, the code must stop before mutating semantic state and print whether it looked for `HF_TOKEN` or cached login credentials. The fixture-based `validate_semantic.py --use-temp-db` path must create and clean up its own temporary database so repeated validation does not pollute `.data/`. The README merge must also be idempotent: re-running the documentation step should not duplicate imported sections, and deleting the repo-local `AGENTS.md` should happen only after its content is safely represented in `README.md`.

## Artifacts and Notes

The implementation should leave behind a small set of inspectable artifacts under `kakaocli-patched/.data/`, for example semantic metadata, semantic checkpoint state, and any local vector payload needed for search. These artifacts must be deterministic enough to debug, but temporary scratch files used only during validation should be deleted before finalizing. The fixture validation path may use a temporary database outside `.data/`, but it must clean that file up automatically. Keep example outputs short and JSON-first because that matches the current repo style. The human-facing document set after completion should be smaller than before: the patched repo keeps `README.md` and removes the duplicate repo-local `AGENTS.md`.

## Interfaces and Dependencies

Use the existing `kakaocli-patched/tools/live_rag` module boundary. The interfaces below are already present in the repository as part of the completed implementation recorded in `Progress`. Treat them as existing contracts to preserve and verify while doing the remaining next-session work. Only extend them if the unfinished operational tasks in this plan truly require it.

In `kakaocli-patched/tools/live_rag/embedding_client.py`, keep the existing small client wrapper with the stable interface:

    class ExternalEmbeddingClient:
        def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
        def embed_query(self, text: str) -> list[float]: ...

This client already uses Hugging Face authentication from `HF_TOKEN` or cached login state, defaults the model to `Qwen/Qwen3-Embedding-8B`, and accepts an optional provider override. The next session should verify that this behavior still holds while the rebuild/default-mode follow-up work proceeds.

In `kakaocli-patched/tools/live_rag/store.py`, preserve the existing semantic-sidecar persistence methods shaped like:

    def iter_messages_for_embedding(self, after_log_id: int | None, limit: int | None) -> list[dict[str, Any]]: ...
    def upsert_semantic_chunks(self, chunks: list[dict[str, Any]]) -> dict[str, int]: ...
    def semantic_search(self, query_vector: list[float], limit: int, chat_id: int | None, speaker: str | None) -> list[dict[str, Any]]: ...

In `kakaocli-patched/tools/live_rag/semantic_index.py`, keep the existing chunk construction and vector scoring helpers. The current chunking rule is simple and explicit: for short Kakao messages, use one message as one chunk; for longer text, split by character count with overlap and retain `log_id`, `chat_id`, `sender`, `timestamp`, and source text in metadata. Change this only if the remaining real-data validation shows a concrete retrieval problem.

In `kakaocli-patched/tools/live_rag/app.py`, keep `/retrieve` aligned with the existing request shape:

    {
      "query": "...",
      "mode": "lexical" | "semantic" | "hybrid",
      "limit": 8,
      "semantic_top_k": 24,
      "chat_id": null,
      "speaker": null,
      "since_days": null,
      "context_before": 2,
      "context_after": 2
    }

In `kakaocli-patched/tools/live_rag/query.py`, keep the existing CLI flags aligned with the service:

    --mode lexical|semantic|hybrid
    --semantic-top-k N
    --since-days DAYS

In `kakaocli-patched/tools/live_rag/build_semantic_index.py`, keep the existing options:

    --mode rebuild|update
    --limit N
    --embedding-model MODEL_ID
    --embedding-provider PROVIDER

In `kakaocli-patched/tools/live_rag/validate_semantic.py`, keep the existing validation entrypoint that can create a temporary fixture database, seed a fixed message set through `LiveRAGStore.ingest_messages`, build the semantic sidecar, and assert that a paraphrased semantic query returns the expected fixture `log_id`. A stable interface such as the following must continue to work:

    conda run -n module python tools/live_rag/validate_semantic.py --use-temp-db

In `kakaocli-patched/README.md`, the final content already directly includes the local operational guidance that used to be isolated in `kakaocli-patched/AGENTS.md`, especially:
- credential storage behavior,
- automatic login and lifecycle behavior,
- app state detection and AX caveats,
- local Live RAG routing and examples,
- troubleshooting guidance,
- safety rules for sending and automation.

In `kakaocli-patched/requirements-live-rag.txt`, keep only the smallest required package set. The current expected set is:

    fastapi
    uvicorn
    huggingface_hub
    numpy

Avoid LangChain, avoid an external vector database, and avoid introducing a second prompt or agent framework. The current service already provides the right surface.

## Change Note

This revised ExecPlan narrows the earlier generic “HF embeddings plus FAISS over arbitrary chat files” idea into a repo-native plan: external embeddings stay, but the source of truth remains the existing Kakao `messages` store, lexical retrieval remains available, and the first semantic index stays local and simple. It also adds an explicit documentation-consolidation requirement: `kakaocli-patched/AGENTS.md` will be merged into `kakaocli-patched/README.md` and then deleted, because the root repository already owns the real `AGENTS.md` rules file.

Revision note, 2026-03-07: after review, this plan was tightened so semantic validation is reproducible on a fixture database, the MD5 flow captures both before and after snapshots explicitly, AGENTS-retirement checks only search the patched repo, and bookkeeping now targets concrete issue/progress files that exist in this workspace.

Revision note, 2026-03-07 (handoff update): semantic feasibility is now proven with `Qwen/Qwen3-Embedding-8B`, the routed provider returns a `(1, 4096)` payload that the parser now accepts, a limited real-data rebuild has succeeded, and a recent lab-chat subset has already produced useful semantic hits. The next session should focus on full real-data coverage, operator-facing default retrieval behavior, the professor-instruction question flow, and MD5 verification on a frozen dataset.

Revision note, 2026-03-07 (state-clarification update): the remaining sections now distinguish between implementation that already exists in the working tree and the smaller set of verification or operational follow-up tasks that are still open. Existing semantic interfaces are described as contracts to preserve and verify, not as greenfield additions to re-implement.
