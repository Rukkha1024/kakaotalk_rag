2026-03-07
- The Live RAG webhook server and `sync --follow` were running as ad-hoc terminal processes, so there was no reboot-safe or on-demand managed startup path for Codex.
- Existing Live RAG databases created before checkpoint state was added had no `last_ingested_log_id`, so restart recovery could not resume explicitly until migration logic backfilled the checkpoint from stored messages.
