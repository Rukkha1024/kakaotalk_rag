# Issue 002: Add topic-first Kakao answer guidance

**Status**: Done
**Created**: 2026-03-08

## Background

Recent KakaoTalk answers were too chronology-first and missed the user's likely
intent when a repeated salient topic should have been surfaced first. The agent
guidance should explicitly prefer the dominant topic or repeated entity before a
raw recent-message dump.

## Acceptance Criteria

- [x] `AGENTS.md` contains a short English rule for topic-first Kakao answers.
- [x] `.agents/skills/kakaocli/SKILL.md` contains the detailed Kakao-specific answer order.
- [x] The guidance stays narrow and does not add unrelated policy text.

## Tasks

- [x] 1. Add a concise global rule to `AGENTS.md`.
- [x] 2. Add the Kakao-specific answer flow to `.agents/skills/kakaocli/SKILL.md`.
- [x] 3. Verify the markdown diff and commit with a Korean message.

## Notes

The global rule should stay simple and in English. The detailed behavior belongs
in the Kakao skill because it applies only to Kakao evidence-backed answers.

## Outcome

Added one short English rule to `AGENTS.md` and the detailed answer order to
`.agents/skills/kakaocli/SKILL.md`. Verified with `git diff --check`.
