# Embedding Rules

## Scope

Apply this file to semantic embedding, semantic index, build, rebuild, and validation work.

## Sources

- Chat metadata: `kakaocli chats --json`
- Messages: `kakaocli-patched/.data/live_rag.sqlite3` `messages`
- Local chat metadata cache: `kakaocli-patched/.data/live_rag.sqlite3` `chat_metadata`
- Semantic sidecar: `kakaocli-patched/.data/live_rag.sqlite3` `semantic_chunks`
- Semantic runtime/config state: `kakaocli-patched/.data/live_rag.sqlite3` `live_rag_state`

## Rules

- Only embed normal text messages: `message_type = 1`
- Exclude trimmed-empty text
- Exclude JSON-like placeholder rows where the full text is wrapped in `{...}`
- Exclude rows with no meaningful `[0-9A-Za-z가-힣]` tokens
- Exclude rows whose meaningful-token character count is less than `2`
- Allow chats with `member_count <= 30` by default
- Exclude chats with `member_count > 30` from semantic candidates
- Build semantic text from chat name, sender, direction, and chunk content
- Semantic config signature must include model, provider, chunking, semantic text template version, embedding rule version, and `max_member_count`

## Required Behavior

- Refresh chat metadata before every semantic build/update
- If chat metadata refresh fails, returns invalid or empty data, or does not cover candidate rows, stop the build
- If candidate messages are missing chat metadata, stop the build before mutating semantic state
- If the embedding rule or any semantic config-signature input changes, rebuild the semantic sidecar
- If `--mode update` sees a semantic config signature mismatch, stop and require `--mode rebuild`
- Keep canonical `messages` unchanged; semantic data belongs in the sidecar tables and runtime state
