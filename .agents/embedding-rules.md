# Embedding Rules

## Scope

Apply this file to semantic embedding, semantic index, build, rebuild, and validation work.

## Sources

- Chat metadata: `kakaocli chats --json`
- Messages: `kakaocli-patched/.data/live_rag.sqlite3` `messages`
- Semantic sidecar: `kakaocli-patched/.data/live_rag.sqlite3` `semantic_chunks`

## Rules

- Only embed normal text messages: `message_type = 1`
- Exclude empty text
- Exclude system, feed, and placeholder rows
- Refresh chat metadata before semantic build/update
- Exclude chats with `member_count > 30`
- Allow chats with `member_count <= 30`

## Required Behavior

- If chat metadata refresh fails, stop the build
- If candidate messages are missing chat metadata, stop the build
- If the embedding rule changes, change the semantic config signature
- If the rule changes, rebuild the semantic sidecar
