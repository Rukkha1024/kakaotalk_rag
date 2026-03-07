# Goal

Set up Codex on this Mac so KakaoTalk work uses a dedicated skill backed by `kakaocli`, and install + verify `kakaocli` if it is missing.

# Constraints

- Use the built-in `$skill-creator` to draft the skill before you finalize the files.
- The global `AGENTS.md` Kakao rule block must be exactly 3 lines.
- Prefer the current user-skill location: `$HOME/.agents/skills`.
- Do not destroy existing unrelated guidance. Merge carefully.
- Never send messages to other people.
- During setup, do not run `kakaocli send`, `kakaocli sync --follow`, or `kakaocli harvest`.
- If a validation step fails, stop and fix it before continuing.
- If blocked by macOS permissions or KakaoTalk login state, stop and report the exact manual step instead of pretending the setup succeeded.

# Deliverables

Create or update these machine-scoped files:

1. `~/.codex/AGENTS.md`
2. `~/.agents/skills/kakaocli-safe-ops/SKILL.md`
3. `~/.agents/skills/kakaocli-safe-ops/agents/openai.yaml`

Also ensure `kakaocli` is installed and run these verification commands if installation succeeds:

- `kakaocli status`
- `kakaocli auth`
- `kakaocli login --status`

# Stop-and-fix rule

After every milestone:
1. run the validation commands for that milestone,
2. if validation fails, repair immediately,
3. only then continue.

Do not leave any item half-done.

# Milestone 1 — Inspect the environment

## Actions

- Confirm this is macOS.
- Inspect whether these already exist:
  - `~/.codex/AGENTS.md`
  - `~/.agents/skills/kakaocli-safe-ops/`
  - `kakaocli`
  - `brew`
- If an existing Kakao-related AGENTS block or skill already exists, preserve it unless it clearly conflicts with this plan. Prefer minimal edits over replacement.
- If you will modify an existing file, create a timestamped backup first in the same parent directory.

## Suggested commands

```bash
uname -s
mkdir -p ~/.codex ~/.agents/skills
test -f ~/.codex/AGENTS.md && echo "HAS_AGENTS=1" || echo "HAS_AGENTS=0"
test -d ~/.agents/skills/kakaocli-safe-ops && echo "HAS_SKILL=1" || echo "HAS_SKILL=0"
command -v kakaocli || true
command -v brew || true
```

## Acceptance criteria

- You know whether AGENTS already exists.
- You know whether the skill already exists.
- You know whether `brew` exists.
- You know whether `kakaocli` exists.

# Milestone 2 — Update global AGENTS guidance

## Target content

If `~/.codex/AGENTS.md` does not exist, create it with exactly this block:

```md
Use $kakaocli-safe-ops for KakaoTalk tasks on this Mac.
For non-Kakao tasks, do not use kakaocli or its skill.
Never send messages to other people without my explicit confirmation.
```

If `~/.codex/AGENTS.md` already exists:
- preserve all unrelated existing content,
- append this exact 3-line Kakao block once if it is not already present,
- do not duplicate it.

## Validation

```bash
grep -F 'Use $kakaocli-safe-ops for KakaoTalk tasks on this Mac.' ~/.codex/AGENTS.md
grep -F 'For non-Kakao tasks, do not use kakaocli or its skill.' ~/.codex/AGENTS.md
grep -F 'Never send messages to other people without my explicit confirmation.' ~/.codex/AGENTS.md
```

# Milestone 3 — Draft the skill with the built-in skill creator, then normalize it

## Required action

Before writing the final skill files, invoke the built-in skill creator and use it as the drafting step.

Use this exact instruction for the creator:

```text
$skill-creator Create an instruction-only user skill named "kakaocli-safe-ops". It is for macOS only. It should trigger when the task involves KakaoTalk, kakaocli, local chat search, login or permissions, or safe reply preparation on this machine. It must know how to install kakaocli, check macOS Full Disk Access and Accessibility, verify kakaocli with status/auth/login --status, prefer read-only JSON commands, never send messages to other people without explicit confirmation, and only use sync or harvest when explicitly requested. The skill should report to the user in Korean unless asked otherwise.
```

If the creator asks follow-up questions, answer them consistently with this plan. After the creator drafts the skill, edit the generated files so they match the exact target content below.

## Write the final skill files

Create or update:

- `~/.agents/skills/kakaocli-safe-ops/SKILL.md`
- `~/.agents/skills/kakaocli-safe-ops/agents/openai.yaml`

### Exact `SKILL.md`

```md
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
```

### Exact `agents/openai.yaml`

```yaml
interface:
  display_name: "KakaoTalk on this Mac"
  short_description: "Install, verify, and safely use kakaocli for KakaoTalk tasks on this Mac."
policy:
  allow_implicit_invocation: true
```

## Validation

```bash
test -f ~/.agents/skills/kakaocli-safe-ops/SKILL.md
grep -F 'name: kakaocli-safe-ops' ~/.agents/skills/kakaocli-safe-ops/SKILL.md
grep -F 'allow_implicit_invocation: true' ~/.agents/skills/kakaocli-safe-ops/agents/openai.yaml
```

## Compatibility note

Current Codex docs use `$HOME/.agents/skills`. If this Codex build does not detect the new skill after restart and there is a legacy `~/.codex/skills` directory, create a symlink there pointing to the same folder instead of duplicating files.

# Milestone 4 — Install kakaocli if it is missing

## Actions

- If `kakaocli` is already available on `PATH`, skip installation.
- If it is missing and `brew` exists, install with:
  `brew install silver-flight-group/tap/kakaocli`
- If that fails, use the documented source-build fallback:
  - `brew install sqlcipher`
  - `git clone https://github.com/silver-flight-group/kakaocli.git`
  - `cd kakaocli`
  - `swift build -c release`
- If source-build succeeds but the binary is not on `PATH`, either:
  - run it directly from `.build/release/kakaocli` for verification, or
  - add it to `PATH` in a minimal, reversible way and report what changed.
- If `brew` is missing, stop and report that blocker clearly.

## Validation

```bash
command -v kakaocli || true
```

# Milestone 5 — Verify the installation and the minimum read path

## Actions

Run these in order:

```bash
kakaocli status
kakaocli auth
kakaocli login --status
```

Interpret the results honestly.

## Rules for this milestone

- Do not run `kakaocli send`.
- Do not run `kakaocli sync --follow`.
- Do not run `kakaocli harvest`.
- If the blocker is Full Disk Access or Accessibility, tell the user the exact settings path.
- If the blocker is missing KakaoTalk login credentials, explain that `kakaocli login` can store them, but do not store them unless the user explicitly asks.

## Acceptance criteria

- `kakaocli` is installed or you reported a real blocker.
- The AGENTS block exists.
- The user skill exists.
- Verification commands were run if installation succeeded.
- No messages were sent.

# Definition of done

Done means all of the following are true:

- `~/.codex/AGENTS.md` contains the exact 3-line Kakao rule block once.
- `~/.agents/skills/kakaocli-safe-ops/SKILL.md` exists with the exact target guidance above.
- `~/.agents/skills/kakaocli-safe-ops/agents/openai.yaml` exists.
- `kakaocli` is installed, or you stopped with a concrete blocker and exact next manual step.
- If installation succeeded, you ran `kakaocli status`, `kakaocli auth`, and `kakaocli login --status`.
- You did not send any messages.

# Final response format

Reply in Korean and include:
1. changed files,
2. exact commands run,
3. what succeeded,
4. what is blocked,
5. the next manual step, if any.

Do not add unrelated refactors or extra files.
