# 이슈 001: 복사된 repo용 portable kakaocli 부트스트랩

**상태**: 완료
**생성일**: 2026-03-07

## 배경

이 repo에는 로컬 KakaoTalk `userId` 탐지 문제를 우회한 패치 버전 `kakaocli`
워크플로가 포함되어 있지만, 현재 설정은 여전히 머신별 절대경로와 수동 지식에
의존합니다. repo를 다른 Mac으로 복사하거나 clone 했을 때 AI 에이전트가
업스트림 Homebrew 바이너리로 새지 않고, repo 자체만으로 패치된 워크플로를
설치하고 검증할 수 있어야 합니다.

## 완료 기준

- [x] 복사된 repo 기준 상대경로로 동작하는 repo-local 설치 명령이 존재한다.
- [x] 설치 흐름이 패치 워크플로에 필요한 런타임 요소인 `sqlcipher`, repo-local
      Python runtime, 로컬 release build를 준비한다.
- [x] repo 문서와 skill이 절대경로나 `PATH` `kakaocli` 대신 repo-local wrapper를
      우선 사용한다.
- [x] 임시 위치로 옮긴 repo에서 portable 흐름이 검증된다.

## 작업 목록

- [x] 1. repo 루트와 `kakaocli-patched/` 내부에 portable 설치 및 wrapper 스크립트를
         추가한다.
- [x] 2. Live RAG helper용 repo-local Python runtime 명세를 재현 가능하게 추가한다.
- [x] 3. README, AGENTS, skill을 portable 진입점 기준으로 갱신한다.
- [x] 4. 임시 위치에 복사한 repo에서 설치 흐름을 검증한다.

## 참고 사항

- repo 루트 wrapper `./install-kakaocli`, `./kakaocli-local`, `./query-kakao`를 추가했다.
- `kakaocli-patched/bin/` 아래에도 동일한 repo-local wrapper를 추가했다.
- Live RAG 부트스트랩은 conda 대신 repo-local `.venv`를 사용하도록 바꿨다.
- `/tmp/codex-portable.5B6SXW` 복사본에서
  `./install-kakaocli --build-only`, `./kakaocli-local auth`,
  `LIVE_RAG_LAUNCHD_LABEL=com.codex.kakaocli-live-rag-copytest LIVE_RAG_BASE_URL=http://127.0.0.1:8766 ./query-kakao --json --query-text "업데이트"`를 검증했다.
