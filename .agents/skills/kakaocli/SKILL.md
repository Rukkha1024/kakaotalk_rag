---
name: kakaocli
description: Use the external kakaocli and query-kakao toolchain on this macOS machine as a default local RAG memory hook for user prompts. Run it before answering when the repo instructions require a global memory lookup, and incorporate relevant evidence when it helps the reply.
---

# Purpose

Use `query-kakao` and `kakaocli` as the assistant's local memory layer on this Mac.
The default goal is not "answer KakaoTalk questions only." The goal is:
- run a lightweight local RAG lookup for user prompts,
- detect whether prior local material is relevant,
- weave relevant evidence into the answer when it improves usefulness,
- stay quiet about the lookup when nothing relevant is found.

This skill is for macOS only.

## Default workflow

For normal assistant replies:
1. Run `query-kakao --json --query-text "<user prompt>"` first.
2. Inspect whether the returned material is actually related to the user's request.
3. If relevant material exists, incorporate it into the answer naturally.
4. If the hits are weak, noisy, or unrelated, answer normally and do not force the RAG output into the reply.

Do not dump raw retrieval output unless the user asks for the raw evidence.

## When to use

Use this skill when:
- the repo instructions require a prompt-time memory lookup,
- the user mentions KakaoTalk, `kakaocli`, `query-kakao`, local chat search, or memory from prior chats,
- the task is to answer with local evidence, inspect chat history, verify login or permissions, or prepare a safe reply workflow.

## Relevance standard

Treat retrieved material as relevant when at least one of these is true:
- the same person, team, project, file, meeting, task, or topic appears in both the prompt and the retrieved material,
- the material answers the exact question or fills in context the user is likely referring to,
- repeated hits point to the same dominant subject.

Treat retrieved material as not relevant when:
- it only overlaps on generic words,
- it points to a different project or person,
- it would distract from a direct answer more than it helps.

When relevance is ambiguous, prefer a normal answer over forcing a weak memory reference.

## Safety rules

- Never send a message to another person unless the user explicitly says to send it now.
- During setup, do not run `send`, `sync --follow`, or `harvest` unless the user explicitly asks.
- Prefer read-only commands with `--json` when the output may be consumed programmatically.
- If a send test is explicitly requested, use `kakaocli send --dry-run ...` first. Use `kakaocli send --me _ ...` only for a self-chat test after the user approves.
- If permissions are missing or KakaoTalk is not logged in, stop and explain the exact manual step.

## Answering style

If relevant evidence exists:
- answer the user's question first,
- fold the evidence into the response in plain language,
- mention the prior material as support, not as the whole answer,
- lead with the dominant topic or repeated entity when the evidence makes that clear,
- support that point with 1-3 concise facts or snippets.

Good pattern:
- `관련 자료를 보면 A 쪽 맥락이 반복해서 나오고, 그래서 이번 요청도 그 연장선으로 보는 게 맞습니다.`

Bad pattern:
- pasting a raw message dump,
- listing irrelevant hits "just in case",
- acting certain when the retrieval is weak.

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
3. For prompt-time memory lookup and evidence-backed answers, prefer:
   `query-kakao --json --query-text "..."`

Interpretation:
- If either command is missing, stop and surface the exact install step instead of guessing alternate repo-relative paths.
- If `auth` succeeds, read commands are ready even without a visible KakaoTalk window.
- If `login --status` shows missing credentials, explain that UI-driven commands may need `kakaocli login` and ask before storing credentials.
- If `status` or `login --status` time out while probing KakaoTalk state, report that explicitly and continue from the `auth` result instead of retrying forever.
- Do not start long-running monitoring as part of basic verification.

## Common commands

Prefer these first:
- `query-kakao --json --query-text "<user prompt>"`
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
- Prompt-time lookup can add latency, so keep it lightweight and avoid repeated retries.

## Reporting

Respond in Korean unless the user asks otherwise.

For answers that used retrieved local evidence:
- do not default to a raw recent-message dump,
- state the dominant topic, repeated entity, or likely intended point first when the evidence makes it clear,
- support that point with 2-4 concrete message snippets in time order or importance order,
- if one topic is clearly repeated, mention that topic before listing supporting details.

Always report:
- exact commands run,
- what succeeded,
- what failed,
- the next manual step if blocked.
