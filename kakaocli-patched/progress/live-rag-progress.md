# Live RAG Progress

## Goal

Enable KakaoTalk live ingestion on this Mac using the patched `kakaocli`, keep a local searchable store, and let Codex answer KakaoTalk questions from that local evidence path.

## Why This Patch Exists

- Upstream `kakaocli` could not open the KakaoTalk SQLCipher database on this Mac, so there was no usable read path for RAG.
- The blocking failure was `auth`: without a valid local Kakao `userId`, `kakaocli` could not derive the database name and encryption key.
- Live RAG depends on a stable read path first. Without that patch, `sync --follow`, `chats`, `messages`, `search`, and any ingestion pipeline were dead on arrival.

## What Was Actually Broken

- `DeviceInfo.userId()` only trusted a narrow set of plist keys.
- The current KakaoTalk macOS state on this machine does not expose the DB `userId` in those plist keys.
- The usable DB `userId` was instead visible in cached `talk-pilsner` HTTP request headers as `talk-user-id`.
- Because of that mismatch, upstream `kakaocli` failed before any RAG ingestion could start.
- After the auth patch, a second problem appeared in the first Live RAG prototype: duplicate backfill of the same chat returned webhook `HTTP 500` because the first FTS update path was not idempotent.

## What Was Still Missing For Codex

- Even after the first local webhook + FTS prototype worked, Codex still did not have a deterministic way to use it during a normal request.
- The webhook server and `sync --follow` were running as ad-hoc terminal processes, so Live RAG disappeared after process exit or reboot.
- There was no Codex-facing query entrypoint that could:
  - ensure the local service is running
  - wait for `/health`
  - query retrieval
  - return evidence-ready results to the agent
- Restart behavior was still ambiguous because the Live RAG layer had no explicit persisted ingestion checkpoint.

## What Was Patched

- Patched `kakaocli` auth so it can fall back from plist parsing to KakaoTalk HTTP cache inspection and recover the correct `userId`.
- Added a local Live RAG ingestion layer on top of the patched binary:
  - FastAPI webhook receiver
  - SQLite message store
  - FTS retrieval index
  - backfill script for recent history
  - live sync runner for `sync --follow --webhook`
- Fixed the duplicate backfill issue by migrating the FTS design to a regular `fts5` table rebuilt from the canonical `messages` table.
- Added reboot-safe Live RAG process management:
  - `tools/live_rag/service_manager.py`
  - `tools/live_rag/supervisor.py`
  - per-user `launchd` LaunchAgent install/load flow
- Added `tools/live_rag/query.py` so Codex can:
  - ensure the background service
  - wait for local health
  - call `/retrieve`
  - receive evidence-ready hits with context
- Added persisted `last_ingested_log_id` state inside the local SQLite store so restart recovery is explicit.
- Added migration logic so older Live RAG databases without checkpoint state bootstrap `last_ingested_log_id` from stored `MAX(log_id)`.
- Updated agent instructions so KakaoTalk information requests go through the local Live RAG query path first.

## Why The Codex Trigger Path Uses `AGENTS.md` + `query.py`

- The main failure mode here was not retrieval quality but trigger reliability.
- For this project, KakaoTalk RAG needs a deterministic path:
  - user asks Codex about KakaoTalk context
  - Codex runs `query.py`
  - `query.py` ensures launchd service health
  - local `/retrieve` returns evidence
  - Codex answers from that evidence
- This is intentionally a persistent instruction path, not a best-effort optional skill trigger only.
- Recent Vercel agent guidance points in the same direction: persistent `AGENTS.md` context works better than relying on skills alone for broad, recurring behaviors, while skills remain more useful for explicit vertical workflows.

## Current Status

- `kakaocli auth`, `chats`, `messages`, and `search` are working with automatic `userId` discovery.
- Local FastAPI webhook receiver is running on `http://127.0.0.1:8765`.
- Live ingestion uses local SQLite/FTS storage at `.data/live_rag.sqlite3`.
- Initial backfill uses read-only `kakaocli messages --json`.
- Continuous updates are wired through `kakaocli sync --follow --webhook ...`.
- Live RAG now has a launchd-backed supervisor so the webhook server and sync follower can restart after login/reboot.
- Codex can query Live RAG through `tools/live_rag/query.py`, which auto-ensures the service before retrieval.
- LaunchAgent path is `~/Library/LaunchAgents/com.codex.kakaocli-live-rag.plist`.
- The current managed service label is `com.codex.kakaocli-live-rag`.

## Completed

- Patched `kakaocli` so DB auth works on this Mac without manual `--user-id`.
- Confirmed release binary can read real KakaoTalk chats.
- Identified the validation target chat: `청주대 연구원 박다훈`.
- Added `tools/live_rag/app.py`, `store.py`, `backfill.py`, and `run_sync.py`.
- Added `tools/live_rag/service_manager.py`, `supervisor.py`, and `query.py` for reboot-safe service management and Codex retrieval.
- Backfilled recent data into the local store and then continued ingesting live updates.
- Verified retrieval with a real hit on query `업데이트`.
- Verified normalized backfill output matches stored export for `청주대 연구원 박다훈` over the last 5 days via MD5.
- Added durable `last_ingested_log_id` checkpoint tracking inside the local store so `sync --follow` can resume after restart.
- Verified that stopping the managed service and then calling `query.py --json --query-text "업데이트"` auto-starts the service again and returns evidence-backed results.
- Recorded the local operational issue and workaround for future runs:
  - `.claude/issue.md`
  - `$troubleshooting`

## In Progress

- Verify launchd auto-start behavior across a real logout/login or full reboot cycle on this Mac.
- Expand backfill coverage if older chats are needed for broader retrieval context.

## Better Next Improvements

- Upstream the `userId` fallback patch into `kakaocli` properly so local forks are not required on this Mac.
- Replace pure lexical retrieval with a better answer pipeline for Codex:
  - rank conversation windows rather than single hit rows only
  - generate a short evidence summary before final answer assembly
- Add richer chat metadata enrichment for `(unknown)` group chats, either via periodic metadata sync or controlled `harvest`.
- Move retrieval from pure lexical FTS toward hybrid retrieval:
  - keep FTS for exact phrase recall
  - add embeddings for semantic recall
  - return conversation windows rather than isolated hits only
- Add richer answer formatting in the Codex query path so evidence can be summarized automatically, not just returned as hits.
- Add explicit service diagnostics to the query path so Codex can report whether a failure came from:
  - Kakao login state
  - webhook health
  - sync follower
  - retrieval store

## Validation Plan

1. Start the webhook server and confirm `/health`.
2. Backfill recent messages from real chats into the local store.
3. Compare normalized backfill payloads with stored exports using MD5.
4. Start `sync --follow --webhook` and confirm the watcher is ready.
5. Stop the managed service, then call `query.py` and confirm it auto-recovers the local Live RAG stack.
6. Validate retrieval with a known query and summarize what `박다훈` said in the last 5 days.

## Latest Verification

- `/health` returned `status=ok`.
- `service_manager.py status` returned:
  - `loaded=true`
  - `launch_agent_exists=true`
  - `message_count=1171`
  - `chat_count=20`
  - `last_ingested_log_id=3790971385111179265`
- `query.py --json --query-text "업데이트"` succeeded after the managed service had first been stopped.
- The managed service came back through `launchd` and restored the local webhook + sync path automatically.
- MD5 check for `박다훈` 5-day dataset matched between normalized source and stored export:
  - `source_md5=009144965cb562d608280643e554949e`
  - `store_md5=009144965cb562d608280643e554949e`
- The current remaining verification gap is a real macOS login/reboot cycle test, not local process recovery.
