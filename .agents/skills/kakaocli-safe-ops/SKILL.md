---
name: kakaocli-safe-ops
description: Install, verify, and safely use kakaocli on this macOS machine for KakaoTalk tasks. Use when the task involves KakaoTalk, kakaocli, local chat search, login or permissions, or preparing a safe reply flow. Do not use for unrelated work.
---

# Purpose

Use `kakaocli` to handle KakaoTalk tasks on this Mac. This skill is for macOS only.

## Local defaults on this Mac

- Default raw CLI path: `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli`
- Default evidence query path: `conda run -n module python /Users/alice/Documents/codex/kakaocli-patched/tools/live_rag/query.py --json --query-text "..."`
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

1. Check whether `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli` already exists. If it does, use it as the default command.
2. If the patched repo exists but the binary is missing, build `/Users/alice/Documents/codex/kakaocli-patched` with `swift build -c release`.
3. Only if the patched repo is unavailable, fall back to the upstream install path:
   `brew install silver-flight-group/tap/kakaocli`
4. Explain that the Homebrew or upstream binary may still fail `auth` on this Mac because upstream `userId` discovery does not include the local cache fallback.
5. Do not claim success until `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli status` runs successfully.

## Permissions

The terminal app needs:
- Full Disk Access for all `kakaocli` commands.
- Accessibility for UI automation commands such as `send`, `harvest`, and `inspect`.

Guide the user to:
- `System Settings > Privacy & Security > Full Disk Access`
- `System Settings > Privacy & Security > Accessibility`

## Verification

Run, in order:
1. `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli status`
2. `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli auth`
3. `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli login --status`
4. For information requests or summaries, prefer:
   `conda run -n module python /Users/alice/Documents/codex/kakaocli-patched/tools/live_rag/query.py --json --query-text "..."`

Interpretation:
- If `auth` succeeds, read commands are ready even without a visible KakaoTalk window.
- If `login --status` shows missing credentials, explain that UI-driven commands may need `kakaocli login` and ask before storing credentials.
- Do not start long-running monitoring as part of basic verification.

## Common read commands

Prefer these first:
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli chats --json`
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli messages --chat "name" --since 1d --json`
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli search "keyword" --json`
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli query "SELECT COUNT(*) FROM NTChatMessage" --json`

## Real-time and UI commands

Use only when the user explicitly requests them:
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli sync --follow`
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli sync --follow --webhook http://localhost:8080/kakao`
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli harvest`
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli harvest --scroll`
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli send ...`
- `/Users/alice/Documents/codex/kakaocli-patched/.build/release/kakaocli send --dry-run ...`

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
