---
name: kakaocli-safe-ops
description: Install, verify, and safely use kakaocli on this macOS machine for KakaoTalk tasks. Use when the task involves KakaoTalk, kakaocli, local chat search, login or permissions, or preparing a safe reply flow. Do not use for unrelated work.
---

# Purpose

Use `kakaocli` to handle KakaoTalk tasks on this Mac. This skill is for macOS only.

## When to use

Use this skill when:
- the user mentions KakaoTalk or `kakaocli`,
- the task is to install `kakaocli`, check permissions, verify login, read chats, search messages, or set up real-time monitoring,
- the task is to prepare a safe reply workflow that the user may approve later.

Do not use this skill for unrelated work.

## Safety rules

- Never send a message to another person unless the user explicitly says to send it now.
- During setup, do not run `send`, `sync --follow`, or `harvest` unless the user explicitly asks.
- Prefer read-only commands with `--json` when the output may be consumed programmatically.
- If a send test is explicitly requested, use `kakaocli send --dry-run ...` first. Use `kakaocli send --me _ ...` only for a self-chat test after the user approves.
- If permissions are missing or KakaoTalk is not logged in, stop and explain the exact manual step.

## Install

1. Check whether `kakaocli` is already on `PATH`.
2. If it is missing and `brew` exists, install with:
   `brew install silver-flight-group/tap/kakaocli`
3. If the Homebrew install fails, use the documented source-build fallback:
   - `brew install sqlcipher`
   - `git clone https://github.com/silver-flight-group/kakaocli.git`
   - `cd kakaocli`
   - `swift build -c release`
4. If `brew` is missing, explain that the recommended install path uses Homebrew and tell the user what to install first.
5. Do not claim success until `kakaocli status` runs successfully.

## Permissions

The terminal app needs:
- Full Disk Access for all `kakaocli` commands.
- Accessibility for UI automation commands such as `send`, `harvest`, and `inspect`.

Guide the user to:
- `System Settings > Privacy & Security > Full Disk Access`
- `System Settings > Privacy & Security > Accessibility`

## Verification

Run, in order:
1. `kakaocli status`
2. `kakaocli auth`
3. `kakaocli login --status`

Interpretation:
- If `auth` succeeds, read commands are ready even without a visible KakaoTalk window.
- If `login --status` shows missing credentials, explain that UI-driven commands may need `kakaocli login` and ask before storing credentials.
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

## Reporting

Respond in Korean unless the user asks otherwise.

Always report:
- exact commands run,
- what succeeded,
- what failed,
- the next manual step if blocked.
