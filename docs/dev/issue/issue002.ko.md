# 이슈 002: 복사된 Codex 환경용 canonical 단일 kakaocli skill

**상태**: 완료
**생성일**: 2026-03-07

## 배경

이전 portability 작업으로 repo 자체는 self-bootstrapping 되지만, 현재 안내는
repo AGENTS 파일과 여러 skill 위치에 나뉘어 있습니다. 이후 다른 Mac 세팅에서는
사용자가 `$CODEX_HOME` 안의 `kakaocli` skill 하나와 AGENTS 파일만 복사하고,
AI 에이전트가 GitHub URL 또는 복사된 repo 기준으로 설치를 끝낼 수 있어야 합니다.

## 완료 기준

- [x] 이 workspace 기준 canonical 단일 skill이 `.agents/skills/kakaocli` 경로에 존재한다.
- [x] 그 skill 하나만으로 패치된 repo의 macOS 설치 및 검증 흐름이 설명된다.
- [x] repo 지침이 `$kakaocli`를 단일 canonical skill 이름으로 가리킨다.
- [x] 새 skill이 유효성 검증을 통과하고 repo wrapper 흐름과 일치한다.

## 작업 목록

- [x] 1. canonical repo-local `.agents/skills/kakaocli` skill을 만든다.
- [x] 2. install, verification, permission handling을 그 skill 하나에
         self-contained 하게 담는다.
- [x] 3. 중복된 global skill과 mirror skill을 제거한다.
- [x] 4. repo 지침을 `$kakaocli` 단일 skill 기준으로 갱신한다.
- [x] 5. skill 검증 후 커밋한다.

## 참고 사항

- canonical skill은 `/Users/alice/Documents/codex/.agents/skills/kakaocli/`에 둔다.
- 중복이던 global skill `/Users/alice/.codex/skills/kakaocli/`는 제거했다.
- 중복이던 `kakaocli-patched/skills/kakaocli/` mirror도 제거했다.
- repo AGENTS 지침은 계속 `$kakaocli` 단일 skill 이름을 사용한다.
