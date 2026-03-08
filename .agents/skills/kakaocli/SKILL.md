---
name: kakaocli
description: Install, verify, and safely use the external kakaocli toolkit on this macOS machine for KakaoTalk tasks from the operator repo. Use when the task involves KakaoTalk, kakaocli, local chat search, login or permissions, or preparing a safe reply flow. Do not use for unrelated work.
---

# Purpose

Use `kakaocli` to handle KakaoTalk tasks on this Mac. This skill is for macOS only.

## Local defaults on this Mac

- Default raw CLI path: `kakaocli`
- Default evidence query path: `query-kakao --json --query-text "..."`
- For KakaoTalk information requests, summaries, or evidence-backed answers, use the Live RAG query path first.
- For installation, permissions, login, `status`, `auth`, and low-level diagnostics, use the raw CLI path.
- This repo no longer vendors the public product source. If these commands are missing, install the external toolkit first.

## When to use

Use this skill when:
- the user mentions KakaoTalk or `kakaocli`,
- the task is to install `kakaocli`, check permissions, verify login, read chats, search messages, answer KakaoTalk questions from local evidence, or set up real-time monitoring,
- the task is to prepare a safe reply workflow that the user may approve later.

Do not use this skill for unrelated work.

## Safety rules

- Never send a message to another person unless the user explicitly says to send it now.
- During setup, do not run `send`, `sync --follow`, or `harvest` unless the user explicitly asks.
- Prefer read-only commands with `--json` when the output may be consumed programmatically.
- If a send test is explicitly requested, use `kakaocli send --dry-run ...` first. Use `kakaocli send --me _ ...` only for a self-chat test after the user approves.
- If permissions are missing or KakaoTalk is not logged in, stop and explain the exact manual step.

## Install

1. Check whether `kakaocli` and `query-kakao` resolve on `PATH`.
2. If `kakaocli` is missing, prefer:
   `brew install silver-flight-group/tap/kakaocli`
3. If `query-kakao` is missing, explain that the separate public toolkit must also be installed or its `bin` directory must be added to `PATH`.
4. Do not claim success until `kakaocli auth` succeeds and `query-kakao --json --query-text "..."` resolves as a command path.

## Permissions

The terminal app needs:
- Full Disk Access for all `kakaocli` commands.
- Accessibility for UI automation commands such as `send`, `harvest`, and `inspect`.

Guide the user to:
- `System Settings > Privacy & Security > Full Disk Access`
- `System Settings > Privacy & Security > Accessibility`

## Verification

Run, in order:
1. `kakaocli auth`
2. `kakaocli login --status`
4. For information requests or summaries, prefer:
   `query-kakao --json --query-text "..."`

Interpretation:
- If either command is missing, stop and surface the exact install step instead of guessing alternate repo-relative paths.
- If `auth` succeeds, read commands are ready even without a visible KakaoTalk window.
- If `login --status` shows missing credentials, explain that UI-driven commands may need `kakaocli login` and ask before storing credentials.
- If `status` or `login --status` time out while probing KakaoTalk state, report that explicitly and continue from the `auth` result instead of retrying forever.
- Do not start long-running monitoring as part of basic verification.

## Common read commands

Prefer these first:
- `kakaocli chats --json`
- `kakaocli messages --chat "name" --since 1d --json`
- `kakaocli search "keyword" --json`
- `kakaocli query "SELECT COUNT(*) FROM NTChatMessage" --json`

## Real-time and UI commands

Use only when the user explicitly requests them:
- `kakaocli sync --follow`
- `kakaocli sync --follow --webhook http://localhost:8080/kakao`
- `kakaocli harvest`
- `kakaocli harvest --scroll`
- `kakaocli send ...`
- `kakaocli send --dry-run ...`

## Known limitations

- macOS only.
- Read history may be incomplete until the chat has been opened on this Mac.
- Group chat names may appear as `(unknown)` until `harvest` captures UI names.
- Text is the most reliable supported message type.
- KakaoTalk allows one Mac login per account.
- This operator repo does not embed the public toolkit, so missing `PATH` commands must be fixed before Kakao tasks can proceed.

## Reporting

Respond in Korean unless the user asks otherwise.

For KakaoTalk information answers:
- do not default to a raw recent-message dump,
- state the dominant topic, repeated entity, or likely intended point first when the evidence makes it clear,
- support that point with 2-4 concrete message snippets in time order or importance order,
- if the user asks "what did X say?" and one topic is clearly repeated, mention that topic before listing recent messages.

Always report:
- exact commands run,
- what succeeded,
- what failed,
- the next manual step if blocked.
