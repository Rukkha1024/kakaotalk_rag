# Embedding Rules

## Purpose

This document defines the repository-wide rules for Kakao Live RAG semantic
embedding. Any semantic embedding, semantic index, build, rebuild, or validation
work must follow this document before code changes or runtime execution.

## Data Sources

- Chat metadata source of truth: `kakaocli chats --json`
- Message source of truth: `kakaocli-patched/.data/live_rag.sqlite3` `messages` table
- Semantic sidecar target: `kakaocli-patched/.data/live_rag.sqlite3` `semantic_chunks` table

## Current Inclusion Rules

Semantic embedding candidates must satisfy all of the following:

1. The row is a normal text message: `message_type = 1`
2. The text is not empty after trimming
3. The row is not a system/feed/photo placeholder style record
4. The chat has refreshed metadata from `kakaocli chats --json`
5. The chat `member_count` is less than or equal to `30`

## Current Exclusion Rules

The semantic builder must exclude any message from embedding when any of the
following is true:

- The chat metadata refresh failed
- The chat metadata is missing for the candidate message
- The chat `member_count` is greater than `30`
- The message is a system/feed/non-text placeholder row

This is a hard repository rule. `member_count > 30` is excluded even if the chat
name looks useful or matches a user keyword.

## Build-Time Requirements

- Semantic build, rebuild, and update must refresh chat metadata first
- If metadata refresh fails, the builder must stop before mutating semantic state
- If embedding rules change, the semantic sidecar config signature must change too
- A rule change requires a semantic rebuild rather than a silent update

## Operational Notes

- The current member threshold is fixed: `member_count > 30` is excluded
- `member_count = 30` is allowed
- The builder should fail closed when metadata is incomplete
- Validation fixtures must inject chat metadata explicitly so the same rules apply
