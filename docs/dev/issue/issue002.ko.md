# 이슈 002: 복사된 Codex 환경용 canonical 단일 kakaocli skill

**상태**: 완료
**생성일**: 2026-03-07

## 배경

이전 portability 작업으로 repo 자체는 self-bootstrapping 되지만, 현재 안내는
repo AGENTS 파일과 여러 skill 위치에 나뉘어 있습니다. 이후 다른 Mac 세팅에서는
사용자가 `$CODEX_HOME` 안의 `kakaocli` skill 하나와 AGENTS 파일만 복사하고,
AI 에이전트가 GitHub URL 또는 복사된 repo 기준으로 설치를 끝낼 수 있어야 합니다.

## 완료 기준

- [x] `$CODEX_HOME/skills/kakaocli` 경로에 canonical 단일 skill이 존재한다.
- [x] 그 skill 하나만으로 패치된 repo의 macOS 설치 및 검증 흐름이 설명된다.
- [x] repo 지침이 `$kakaocli`를 단일 canonical skill 이름으로 가리킨다.
- [x] 새 skill이 유효성 검증을 통과하고 repo wrapper 흐름과 일치한다.

## 작업 목록

- [x] 1. canonical global `kakaocli` skill을 만든다.
- [x] 2. clone, copy, install, verification, permission handling을 그 skill 하나에
         self-contained 하게 담는다.
- [x] 3. repo 지침을 `$kakaocli` 단일 skill 기준으로 갱신한다.
- [x] 4. skill 검증 후 커밋한다.

## 참고 사항

- canonical global skill을 `/Users/alice/.codex/skills/kakaocli/`에 만들었다.
- 같은 self-contained 정의를 `kakaocli-patched/skills/kakaocli/`에도 mirror 해서 repo에서 추적 가능하게 했다.
- repo AGENTS 지침이 `$kakaocli` 단일 skill 이름을 사용하도록 갱신했다.
