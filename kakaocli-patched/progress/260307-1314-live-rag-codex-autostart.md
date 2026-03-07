# Live RAG Codex Autostart

## Goal

- Make Codex answer KakaoTalk-related questions from local Live RAG evidence without requiring manual webhook or sync startup after terminal exit, logout, or reboot.

## What Was The Problem

- The first Live RAG prototype proved ingestion and retrieval, but Codex still had no deterministic request path into that local store.
- The webhook server and `kakaocli sync --follow` were ad-hoc terminal processes, so the RAG path disappeared once those processes exited.
- Restart recovery was ambiguous because the local store had no persisted ingestion checkpoint.
- That meant the user goal was still unmet: even with working local retrieval, Codex could not reliably answer from KakaoTalk evidence on demand.

## What Was Done

- Added a launchd-backed service path with:
  - `tools/live_rag/service_manager.py`
  - `tools/live_rag/supervisor.py`
  - `~/Library/LaunchAgents/com.codex.kakaocli-live-rag.plist`
- Added `tools/live_rag/query.py` as the Codex-facing entrypoint.
- Updated the local SQLite store to persist `last_ingested_log_id`.
- Added migration logic so older stores bootstrap the checkpoint from stored `MAX(log_id)`.
- Updated local agent instructions so KakaoTalk information requests use the Live RAG query path first.
- Added a reusable local skill for future progress-note creation:
  - `.agents/skills/progress-md-workflow`
  - timestamped file scaffold script
  - Vercel-inspired guidance reference

## Design Motive

- The trigger path follows the Vercel pattern, but with a local modification.
- Vercel's January 27, 2026 article reported that persistent `AGENTS.md` context outperformed skills alone for broad recurring behavior because the agent no longer had to decide whether to load the guidance.
- This workspace therefore uses:
  - `AGENTS.md` for always-on Kakao Live RAG query behavior
  - a dedicated skill only for explicit repeated workflows such as progress-note creation
- The local modification is stronger naming and structure enforcement:
  - progress files use `YYMMDD-HHMM-subject.md`
  - progress notes must explain the problem, the work, the validation, and future improvements

## Validation

- `conda run -n module python tools/live_rag/service_manager.py status`
  - confirmed `loaded=true`, `launch_agent_exists=true`
- `conda run -n module python tools/live_rag/service_manager.py stop`
  - stopped the managed service cleanly
- `conda run -n module python tools/live_rag/query.py --json --query-text "업데이트"`
  - auto-started the service through launchd and returned retrieval hits
- MD5 re-check for `청주대 연구원 박다훈` over the last 5 days matched between normalized source and stored export
  - `009144965cb562d608280643e554949e`

## Future Improvements

- Run a real logout/login or full reboot verification instead of relying only on local process recovery tests.
- Improve the Codex answer path from lexical hits to conversation-window summaries.
- Add richer metadata enrichment for `(unknown)` chats.
- Extend the new progress-note skill with optional commit and artifact capture if that becomes a repeated need.

## Artifacts

- Repo commits:
  - `3d984ef` for launchd supervision, checkpoint recovery, and Codex query integration
  - `9ed98ac` for the revised cumulative progress document
- Primary cumulative note:
  - `progress/live-rag-progress.md`

## References

- Vercel blog: `AGENTS.md` outperforms skills in our agent evals
  - https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
- Vercel docs: Agent Resources
  - https://vercel.com/docs/agent-resources
- Vercel Labs: Skills
  - https://github.com/vercel-labs/skills
