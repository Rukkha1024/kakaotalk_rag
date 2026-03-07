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
- [ ] Validation is partially complete (completed: dependency install, wrapper rebuild, lexical smoke test, service restart, AGENTS-retirement grep, structured semantic failure checks; remaining: successful semantic build/query with a token that has provider permission, and MD5 capture on a quiescent dataset so live sync does not change the slice mid-run).

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

- Observation: the `/messages?limit=200` MD5 changed across the before/after snapshots because live ingestion continued while implementation was in progress.
  Evidence: both exports still contained 200 items, but the newest and oldest `log_id` values shifted between captures, which indicates ingestion drift rather than a response-shape regression.

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

## Outcomes & Retrospective

Implementation is now in place. The patched repo has one operator-facing guide in `kakaocli-patched/README.md`, the duplicate repo-local `AGENTS.md` file is gone, and the Live RAG code path now includes semantic-sidecar build/update scripts plus `lexical`, `semantic`, and `hybrid` retrieval modes in the service and CLI. Lexical behavior still works through the managed wrapper after a service restart. The remaining gap is not code shape but environment proof: this Mac's cached Hugging Face credentials do not currently have inference-provider permission, so the deterministic semantic validation and a real semantic index build are blocked until a suitable token is supplied. The MD5 comparison also needs to be rerun against a quiet or frozen dataset because live sync kept ingesting newer rows during the implementation window.

## Context and Orientation

The relevant implementation lives under `kakaocli-patched/tools/live_rag`. The file `store.py` is the current local database layer. It stores normalized Kakao messages, an FTS index for keyword search, and the checkpoint used to resume live sync. The file `app.py` exposes `/health`, `/messages`, `/kakao`, and `/retrieve`. The file `query.py` is the command-line entrypoint that ensures the background service is running and then submits a retrieval request. The file `backfill.py` imports older messages from `kakaocli`, while `run_sync.py` keeps live ingestion moving forward.

The relevant human-facing docs currently live in two places inside the patched repo: `kakaocli-patched/README.md` and `kakaocli-patched/AGENTS.md`. The root repository already has its own top-level `AGENTS.md`, which is the actual rules file for work in this workspace. Because of that, the patched repo’s `AGENTS.md` should be treated as an operational document, not as a second authority on agent rules. In this plan, that operational content will be merged into `README.md`, and the repo-local `AGENTS.md` file will be deleted.

In this plan, “semantic retrieval” means finding text by similar meaning rather than by exact shared words. An “embedding” is a list of numbers produced by a model so that semantically similar texts land near each other. A “chunk” is a smaller search unit derived from one message or a short local message window so that long or noisy chat history does not become one giant vector. A “hybrid retrieval” result is a combined ranking that uses both exact keyword evidence and semantic similarity.

The first-pass scope deliberately avoids adding generic `.txt`, `.md`, `.json`, and `.jsonl` transcript import. This repo already has a cleaner message source: the Kakao message rows in `live_rag.sqlite3`. If external transcript import is ever needed, it should be a separate issue after this change proves useful.

The user-facing query wrapper is `/Users/alice/Documents/codex/query-kakao`, which delegates to `kakaocli-patched/bin/query-kakao`. That wrapper runs the patched repo’s `.venv`, not the `module` conda environment directly, and it calls `./bin/install-kakaocli --build-only` when the local runtime is missing or stale. Because of that, dependency edits in `kakaocli-patched/requirements-live-rag.txt` must be validated through both direct `conda run -n module python ...` development commands and the wrapper path that operators actually use.

## Plan of Work

The first milestone is documentation consolidation before behavior changes. Update `kakaocli-patched/README.md` so it directly contains the repo-local operational material that is currently stranded in `kakaocli-patched/AGENTS.md`, including credential storage behavior, automatic lifecycle management, app state detection, AX quirks, Live RAG routing, troubleshooting, and safety rules. Remove README links that tell readers to “see AGENTS.md” for local guidance. Once the README fully carries that content, delete `kakaocli-patched/AGENTS.md`. This is not a pure cosmetic step: it removes a second misleading `AGENTS.md` file from inside a repo that already sits under a higher-level `AGENTS.md`.

The second milestone is a local semantic index builder that does not disturb current ingestion. Add `kakaocli-patched/tools/live_rag/embedding_client.py` to wrap Hugging Face embedding calls. It must accept either `HF_TOKEN` from the environment or the token cached by `hf auth login`, and it must expose one method for document embeddings and one method for query embeddings. Add `kakaocli-patched/tools/live_rag/semantic_index.py` to define chunking, vector serialization, cosine similarity scoring, and index state. Extend `kakaocli-patched/tools/live_rag/store.py` so the same SQLite database can persist chunk metadata, model identity, and embedding checkpoint state. The canonical message rows remain untouched; semantic rows are a sidecar built from them.

The third milestone is a retrieval API that preserves current behavior. Extend `kakaocli-patched/tools/live_rag/app.py` so `/retrieve` accepts a `mode` field with values `lexical`, `semantic`, or `hybrid`. The existing lexical implementation remains the default safe path. Add a semantic retrieval path that embeds the incoming query, scores local chunks, expands matched chunks back to surrounding Kakao messages, and returns the same response shape already used by `query.py`. Add a hybrid path that combines the lexical list and semantic list using a simple rank-combination method that is stable across score scales. The response must still be easy to inject into an LLM prompt because that is how this repo already uses retrieval.

The fourth milestone is operator usability and safety. Extend `kakaocli-patched/tools/live_rag/query.py` to accept `--mode`, `--semantic-top-k`, and `--since-days` so recency filtering is explicit instead of implied. Add a new script `kakaocli-patched/tools/live_rag/build_semantic_index.py` that can perform a full rebuild or an incremental update from the existing message store, and make that script accept the configurable embedding model and provider. Update `kakaocli-patched/requirements-live-rag.txt` with the smallest useful dependency set, expected to be `huggingface_hub` and `numpy`, and avoid adding larger frameworks. Update `kakaocli-patched/README.md` so future operators understand token setup, model selection, the difference between lexical and semantic search, and the exact commands to run from the `module` conda environment. Because `./bin/query-kakao` uses the repo-local `.venv`, this milestone must also keep `./bin/install-kakaocli` compatible so the wrapper still works after dependency changes.

The fifth milestone is validation and repo bookkeeping. Add a small validation script such as `kakaocli-patched/tools/live_rag/validate_semantic.py` that creates an isolated temporary database, seeds a fixed Kakao-like message fixture, proves one document embedding call succeeds, proves one local index build succeeds, and proves one paraphrased query returns the expected fixture hit. Keep a separate smoke check against the real Live RAG database for lexical behavior and wrapper usability, but do not make a fixed live semantic query the primary acceptance criterion. Capture a reference export from the stable `/messages` endpoint before the semantic work and again after it, then compare MD5 hashes so we can prove the canonical ingestion output did not change. After the README consolidation, run a repository search only inside `kakaocli-patched/` to confirm there are no remaining references to `kakaocli-patched/AGENTS.md`. Record implementation notes and blockers in `docs/issue/issue003.md` and `docs/dev/issue/issue003.ko.md`; if the work uncovers a reusable environment workaround worth preserving separately, add a timestamped Markdown note under `kakaocli-patched/progress/`. Remove temporary artifacts, and create the required Korean git commit only after the implementation has been reviewed and accepted.

## Concrete Steps

All commands below assume the working directory is `/Users/alice/Documents/codex/kakaocli-patched` unless a command explicitly says otherwise.

1. Create tracking documents before code changes.

    cd /Users/alice/Documents/codex
    ls docs/issue | sort
    ls docs/dev/issue | sort

2. Consolidate the patched repo documentation before semantic code changes.

    cd /Users/alice/Documents/codex/kakaocli-patched
    rg -n "AGENTS.md" README.md AGENTS.md

    Expected result:
      README.md shows the old links that must be removed.
      AGENTS.md is still present at this point and will be merged then deleted.

3. Install or update Python dependencies inside the required conda environment.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module pip install -r requirements-live-rag.txt

4. Refresh the repo-local wrapper runtime, confirm the current local service works, and capture the baseline output before touching retrieval.

    cd /Users/alice/Documents/codex/kakaocli-patched
    ./bin/install-kakaocli --build-only
    conda run -n module python tools/live_rag/service_manager.py ensure
    curl -s http://127.0.0.1:8765/messages?limit=200 > /tmp/live_rag_messages_before.json
    md5 /tmp/live_rag_messages_before.json
    ./bin/query-kakao --json --query-text "업데이트"

    Expected success shape:
      {"query":"업데이트","hits":[...]}
    Expected failure shape if auth is broken:
      Failed to query live RAG: ...

5. Build or refresh the semantic sidecar from existing Kakao messages.

    cd /Users/alice/Documents/codex/kakaocli-patched
    HF_TOKEN=... conda run -n module python tools/live_rag/build_semantic_index.py --mode rebuild --limit 500

    Expected success shape:
      {"status":"ok","embedded_chunks":500,"updated_from_log_id":12345,"model":"Qwen/Qwen3-Embedding-8B"}

6. Run the deterministic semantic validation script against a temporary fixture database.

    cd /Users/alice/Documents/codex/kakaocli-patched
    HF_TOKEN=... conda run -n module python tools/live_rag/validate_semantic.py --use-temp-db

    Expected success shape:
      {"status":"ok","fixture_query":"회의 연기된 내용","expected_log_id":123,"semantic_hit_log_ids":[123,...]}
    Expected failure shape if Hugging Face auth is missing:
      {"status":"error","stage":"embed_documents","message":"..."}

7. Optionally smoke-test semantic mode and hybrid mode against the real local database after the fixture test passes.

    cd /Users/alice/Documents/codex/kakaocli-patched
    HF_TOKEN=... conda run -n module python tools/live_rag/query.py --mode semantic --json --query-text "<paraphrase of a known real message>"
    HF_TOKEN=... conda run -n module python tools/live_rag/query.py --mode hybrid --json --query-text "<same paraphrase>"

    Expected result:
      The commands return JSON with `"mode":"semantic"` and `"mode":"hybrid"`.
      Hit counts may vary with the operator's actual Kakao history, so this step is a smoke check, not the primary semantic proof.

8. Capture stable output and compare MD5 before and after.

    cd /Users/alice/Documents/codex/kakaocli-patched
    curl -s http://127.0.0.1:8765/messages?limit=200 > /tmp/live_rag_messages_after.json
    md5 /tmp/live_rag_messages_before.json
    md5 /tmp/live_rag_messages_after.json

    Expected result:
      The MD5 hashes match if canonical message output is unchanged.
      If they do not match, stop and explain whether the difference is ordering, formatting, or unintended ingestion drift.

9. Confirm that the repo-local AGENTS file is fully retired.

    cd /Users/alice/Documents/codex
    rg -n "kakaocli-patched/AGENTS.md|\\[AGENTS\\.md\\]\\(AGENTS\\.md\\)|See \\[AGENTS\\.md\\]" /Users/alice/Documents/codex/kakaocli-patched

    Expected result:
      No remaining references inside `kakaocli-patched/README.md` or other patched-repo docs that require the deleted repo-local AGENTS file.

10. Update the concrete issue records that already exist for this work.

    cd /Users/alice/Documents/codex
    sed -n '1,120p' docs/issue/issue003.md
    sed -n '1,120p' docs/dev/issue/issue003.ko.md

    Expected result:
      Record the implementation notes, blockers, and final validation summary in those two issue files.
      If a separate reusable workaround note is needed, create it under `kakaocli-patched/progress/YYMMDD-HHMM-*.md`.

## Validation and Acceptance

Acceptance is behavioral. The change is accepted only if all of the following are true.

- The existing lexical query path still returns hits for an exact keyword query through `tools/live_rag/query.py`.
- `./bin/query-kakao --json --query-text "업데이트"` still works after the dependency and retrieval changes, proving the repo-local wrapper path remains healthy.
- `tools/live_rag/validate_semantic.py --use-temp-db` returns the expected fixture hit for a paraphrased query in `semantic` mode.
- `hybrid` mode returns a merged result list using the same response schema as the current retrieval path.
- Restarting the service does not lose the semantic sidecar state because it is persisted under `.data/`.
- Incremental index refresh only processes newly ingested message rows, or clearly and safely performs a rebuild when configuration changes.
- The `/messages` endpoint output remains stable before and after the semantic work, as shown by MD5 comparison on the same reference slice.
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

Use the existing `kakaocli-patched/tools/live_rag` module boundary.

In `kakaocli-patched/tools/live_rag/embedding_client.py`, define a small client wrapper with a stable interface such as:

    class ExternalEmbeddingClient:
        def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
        def embed_query(self, text: str) -> list[float]: ...

This client must use Hugging Face authentication from `HF_TOKEN` or cached login state, default the model to `Qwen/Qwen3-Embedding-8B`, and accept an optional provider override.

In `kakaocli-patched/tools/live_rag/store.py`, add semantic-sidecar persistence with methods shaped like:

    def iter_messages_for_embedding(self, after_log_id: int | None, limit: int | None) -> list[dict[str, Any]]: ...
    def upsert_semantic_chunks(self, chunks: list[dict[str, Any]]) -> dict[str, int]: ...
    def semantic_search(self, query_vector: list[float], limit: int, chat_id: int | None, speaker: str | None) -> list[dict[str, Any]]: ...

In `kakaocli-patched/tools/live_rag/semantic_index.py`, define chunk construction and vector scoring helpers. Keep the chunking rule simple and explicit: for short Kakao messages, use one message as one chunk; for longer text, split by character count with overlap and retain `log_id`, `chat_id`, `sender`, `timestamp`, and source text in metadata.

In `kakaocli-patched/tools/live_rag/app.py`, extend `/retrieve` so it accepts:

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

In `kakaocli-patched/tools/live_rag/query.py`, add CLI flags:

    --mode lexical|semantic|hybrid
    --semantic-top-k N
    --since-days DAYS

In `kakaocli-patched/tools/live_rag/build_semantic_index.py`, accept:

    --mode rebuild|update
    --limit N
    --embedding-model MODEL_ID
    --embedding-provider PROVIDER

In `kakaocli-patched/tools/live_rag/validate_semantic.py`, define a validation entrypoint that can create a temporary fixture database, seed a fixed message set through `LiveRAGStore.ingest_messages`, build the semantic sidecar, and assert that a paraphrased semantic query returns the expected fixture `log_id`. A stable interface such as the following is sufficient:

    conda run -n module python tools/live_rag/validate_semantic.py --use-temp-db

In `kakaocli-patched/README.md`, the final content must directly include the local operational guidance currently isolated in `kakaocli-patched/AGENTS.md`, especially:
- credential storage behavior,
- automatic login and lifecycle behavior,
- app state detection and AX caveats,
- local Live RAG routing and examples,
- troubleshooting guidance,
- safety rules for sending and automation.

In `kakaocli-patched/requirements-live-rag.txt`, add only the smallest required packages. The current expected set is:

    fastapi
    uvicorn
    huggingface_hub
    numpy

Avoid LangChain, avoid an external vector database, and avoid introducing a second prompt or agent framework. The current service already provides the right surface.

## Change Note

This revised ExecPlan narrows the earlier generic “HF embeddings plus FAISS over arbitrary chat files” idea into a repo-native plan: external embeddings stay, but the source of truth remains the existing Kakao `messages` store, lexical retrieval remains available, and the first semantic index stays local and simple. It also adds an explicit documentation-consolidation requirement: `kakaocli-patched/AGENTS.md` will be merged into `kakaocli-patched/README.md` and then deleted, because the root repository already owns the real `AGENTS.md` rules file.

Revision note, 2026-03-07: after review, this plan was tightened so semantic validation is reproducible on a fixture database, the MD5 flow captures both before and after snapshots explicitly, AGENTS-retirement checks only search the patched repo, and bookkeeping now targets concrete issue/progress files that exist in this workspace.
