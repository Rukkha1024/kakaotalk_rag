---
name: kakaocli
description: Install, verify, and safely use the patched kakaocli workflow from a GitHub URL or copied repo on macOS. Use when Codex needs to clone or locate the repo, run the repo-local wrappers (`install-kakaocli`, `kakaocli-local`, `query-kakao`), troubleshoot KakaoTalk permissions or login, or answer KakaoTalk questions from local evidence without defaulting to Homebrew or PATH kakaocli.
---

# kakaocli

## Overview

Use this skill as the single source of truth for setting up the patched
`kakaocli` repo on another Mac. Do not rely on other skills or repo AGENTS files
to complete install, verification, or read-only KakaoTalk access.

## Repo Discovery

Find the repo before doing anything else.

1. If the current directory has `./install-kakaocli`, treat it as the repo root.
2. Else if the current directory has `./kakaocli-patched/bin/install-kakaocli`,
   treat the current directory as the copied outer repo root.
3. Else if the user gave a GitHub URL, clone it and then move into the cloned repo.
4. Else ask the user for the repo path or GitHub URL.

Use fast checks:

```bash
test -x ./install-kakaocli
test -x ./kakaocli-patched/bin/install-kakaocli
git clone <repo-url>
```

## Canonical Commands

Prefer the repo-root wrappers whenever they exist:

```bash
./install-kakaocli
./kakaocli-local auth
./query-kakao --json --query-text "업데이트"
```

If only `kakaocli-patched/` is available, use:

```bash
./bin/install-kakaocli
./bin/kakaocli-local auth
./bin/query-kakao --json --query-text "업데이트"
```

Do not default to Homebrew or `PATH` `kakaocli` while these repo-local wrappers
exist.

## Install Workflow

Run the smallest path that gets the repo ready:

1. From the repo root, run `./install-kakaocli`.
2. Let the installer handle `sqlcipher`, the repo-local `.venv`, and the patched
   release build.
3. If the repo is unavailable and the user only wants upstream `kakaocli`, explain
   that it may miss the local `userId` cache fallback and can fail `auth`.

Fresh clone flow:

```bash
git clone <repo-url>
cd <repo-dir>
./install-kakaocli
```

## Verification

Run verification in this order:

1. `./kakaocli-local auth`
2. `./kakaocli-local login --status`
3. `./query-kakao --json --query-text "<request>"`

Interpretation:

- Treat `auth` success as the main read-path check.
- Treat `login --status` timeout as non-fatal if `auth` succeeded.
- Treat empty `query-kakao` hits as a valid query result, not an install failure.

## Manual Blockers

Stop and report the exact manual step when setup is blocked:

- Install `KakaoTalk.app` if it is missing.
- Grant `Full Disk Access` to the terminal:
  `System Settings > Privacy & Security > Full Disk Access`
- Grant `Accessibility` only before `send`, `harvest`, or `inspect`:
  `System Settings > Privacy & Security > Accessibility`
- If credentials are missing and the user approves storing them, run:
  `./kakaocli-local login --email <email> --password <password>`
- KakaoTalk allows one Mac login per account.

## Safe Routing

Use the commands below by default:

- Information lookups and summaries: `./query-kakao --json --query-text "..."`
- Diagnostics and raw reads: `./kakaocli-local status|auth|chats|messages|search|query`
- Install and bootstrap: `./install-kakaocli`

Do not run these during setup unless the user explicitly asks:

- `send`
- `sync --follow`
- `harvest`

Never send a message to another person without explicit confirmation.

## Reporting

Respond in Korean unless the user asks otherwise.

Always report:

- exact commands run
- what succeeded
- what failed
- the next manual step if blocked
