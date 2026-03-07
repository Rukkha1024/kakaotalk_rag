# 이슈 002: Kakao 답변의 topic-first 가이드 추가

**상태**: 완료
**생성일**: 2026-03-08

## 배경

최근 KakaoTalk 답변이 시간순 나열에 치우쳐, 반복적으로 등장한 핵심
주제나 사용자가 기대했을 가능성이 높은 포인트를 먼저 드러내지 못했습니다.
원시 최근 메시지 dump보다, 먼저 salient topic을 말하도록 지침을
명시할 필요가 있습니다.

## 완료 기준

- [x] `AGENTS.md`에 짧은 영어 규칙이 추가된다.
- [x] `.agents/skills/kakaocli/SKILL.md`에 Kakao 전용 답변 순서가 추가된다.
- [x] 지침은 이 범위에만 머물고, 관련 없는 정책은 늘리지 않는다.

## 작업 목록

- [x] 1. `AGENTS.md`에 간단한 전역 규칙을 추가한다.
- [x] 2. `.agents/skills/kakaocli/SKILL.md`에 Kakao 전용 답변 흐름을 추가한다.
- [x] 3. markdown diff를 확인하고 한국어 커밋 메시지로 기록한다.

## 참고 사항

전역 규칙은 짧고 영어로 유지한다. 자세한 동작은 Kakao 근거 답변에만
적용되므로 Kakao skill 문서에 둔다.

## 결과

`AGENTS.md`에는 짧은 영어 규칙을 추가했고,
`.agents/skills/kakaocli/SKILL.md`에는 자세한 답변 순서를 추가했다.
검증은 `git diff --check`로 완료했다.
