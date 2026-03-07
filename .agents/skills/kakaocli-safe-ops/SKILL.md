---
name: kakaocli-safe-ops
description: Install, verify, and safely use kakaocli on this macOS machine for KakaoTalk tasks. Use when the task involves KakaoTalk, kakaocli, local chat search, login or permissions, or preparing a safe reply flow. Do not use for unrelated work.
---

# Purpose

Use `kakaocli` to handle KakaoTalk tasks on this Mac. This skill is for macOS only.

## Local defaults on this Mac

- From the repo root, default installer: `./install-kakaocli`
- From the repo root, default raw CLI path: `./kakaocli-local`
- From the repo root, default evidence query path: `./query-kakao --json --query-text "..."`
- If you are already inside `kakaocli-patched/`, use `./bin/install-kakaocli`, `./bin/kakaocli-local`, and `./bin/query-kakao`
- For KakaoTalk information requests, summaries, or evidence-backed answers, use the Live RAG query path first.
- For installation, permissions, login, `status`, `auth`, and low-level diagnostics, use the raw CLI path.
- Do not treat the Homebrew or `PATH` `kakaocli` as the default on this Mac. It may still point to the upstream build without the local `userId` cache fallback.

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

1. From the repo root, run `./install-kakaocli`. If you are already in `kakaocli-patched/`, run `./bin/install-kakaocli`.
2. The installer resolves repo-relative paths, ensures Homebrew `sqlcipher`, prepares the repo-local `.venv` for Live RAG helpers, and builds the patched release binary when needed.
3. Only if the patched repo is unavailable, fall back to the upstream install path:
   `brew install silver-flight-group/tap/kakaocli`
4. Explain that the Homebrew or upstream binary may still fail `auth` on this Mac because upstream `userId` discovery does not include the local cache fallback.
5. Do not claim success until `./kakaocli-local auth` or `./bin/kakaocli-local auth` succeeds.

## Permissions

The terminal app needs:
- Full Disk Access for all `kakaocli` commands.
- Accessibility for UI automation commands such as `send`, `harvest`, and `inspect`.

Guide the user to:
- `System Settings > Privacy & Security > Full Disk Access`
- `System Settings > Privacy & Security > Accessibility`

## Verification

Run, in order:
1. `./install-kakaocli`
2. `./kakaocli-local auth`
3. `./kakaocli-local login --status`
4. For information requests or summaries, prefer:
   `./query-kakao --json --query-text "..."`

Interpretation:
- If `auth` succeeds, read commands are ready even without a visible KakaoTalk window.
- If `login --status` shows missing credentials, explain that UI-driven commands may need `kakaocli login` and ask before storing credentials.
- If `status` or `login --status` time out while probing KakaoTalk state, report that explicitly and continue from the `auth` result instead of retrying forever.
- Do not start long-running monitoring as part of basic verification.

## Common read commands

Prefer these first:
- `./kakaocli-local chats --json`
- `./kakaocli-local messages --chat "name" --since 1d --json`
- `./kakaocli-local search "keyword" --json`
- `./kakaocli-local query "SELECT COUNT(*) FROM NTChatMessage" --json`

## Real-time and UI commands

Use only when the user explicitly requests them:
- `./kakaocli-local sync --follow`
- `./kakaocli-local sync --follow --webhook http://localhost:8080/kakao`
- `./kakaocli-local harvest`
- `./kakaocli-local harvest --scroll`
- `./kakaocli-local send ...`
- `./kakaocli-local send --dry-run ...`

## Known limitations

- macOS only.
- Read history may be incomplete until the chat has been opened on this Mac.
- Group chat names may appear as `(unknown)` until `harvest` captures UI names.
- Text is the most reliable supported message type.
- KakaoTalk allows one Mac login per account.
- The `PATH` `kakaocli` may still be the upstream Homebrew build and should not be assumed to match the patched local repo.

## Reporting

Respond in Korean unless the user asks otherwise.

Always report:
- exact commands run,
- what succeeded,
- what failed,
- the next manual step if blocked.
