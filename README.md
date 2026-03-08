# Codex Kakao Operator Repo

이 저장소는 공개용 `kakaocli` 제품 저장소가 아니라, Codex가 카카오톡 질문에
외부 `kakaocli` 도구를 사용해 답하도록 돕는 운영자용 agent 작업공간입니다.

## 이 저장소의 역할

- `AGENTS.md`와 `.agents/skills/`로 Codex의 Kakao 작업 규칙을 정의합니다.
- 루트 래퍼 `./install-kakaocli`, `./kakaocli-local`, `./query-kakao`로 외부 `PATH`
  명령을 점검하거나 위임합니다.
- 운영 메모, 이슈 문서, progress 기록을 이 저장소에 유지합니다.

공개용 제품 코드는 이 저장소에 내장하지 않습니다. 현재 Mac에서 분리한 공개용
레포는 `/Users/alice/Documents/kakaocli-public`에 따로 있습니다.

## Quick Start

### 1. 외부 toolkit 확인

먼저 아래 래퍼를 실행합니다.

```bash
./install-kakaocli
```

이 래퍼는 제품을 빌드하지 않습니다. 대신 외부 `PATH` 명령 `kakaocli`와
`query-kakao`가 준비되었는지 확인하고, 빠진 명령이 있으면 설치 방향을
안내합니다.

### 2. 기본 점검

```bash
./kakaocli-local status
./kakaocli-local auth
./kakaocli-local login --status
```

권한이 빠져 있으면 macOS에서 아래를 확인합니다.

- Full Disk Access
- Accessibility

### 3. 근거 기반 질의

카카오톡 정보 조회나 요약은 아래 경로를 기본으로 사용합니다.

```bash
./query-kakao --json --query-text "박다훈 업데이트"
./query-kakao --json --mode hybrid --query-text "박다훈이 미룬 일정"
```

이 래퍼는 외부 `query-kakao` 명령으로 위임합니다. 명령이 없으면 먼저
`./install-kakaocli`를 다시 실행해 누락된 설치 단계를 확인합니다.

## 외부 의존 관계

이 저장소는 외부 설치를 전제로 합니다.

- 핵심 CLI: `kakaocli`
- 근거 기반 질의 진입점: `query-kakao`

`kakaocli`가 없다면 보통 아래부터 확인합니다.

```bash
brew install silver-flight-group/tap/kakaocli
```

그 뒤에도 `query-kakao`가 없다면, 분리된 공개용 toolkit의 `bin` 경로가 `PATH`에
노출되어 있는지 확인해야 합니다.

## 운영 규칙

- KakaoTalk 정보 요청은 먼저 `./query-kakao --json --query-text "<request>"`로 시작합니다.
- 설치/권한/login/status/auth/저수준 진단은 `./kakaocli-local`로 처리합니다.
- 래퍼가 missing command를 보고하면, 임의의 repo-relative 경로를 추정하지 말고
  정확한 설치 누락 상태를 먼저 사용자에게 알려야 합니다.
- 다른 사람에게 메시지를 보내는 명령은 기존처럼 명시적 사용자 확인이 있어야 합니다.

## 참고

- 운영자용 지침: `AGENTS.md`
- Kakao 전용 스킬: `.agents/skills/kakaocli/SKILL.md`
- 분리된 공개용 toolkit 로컬 위치: `/Users/alice/Documents/kakaocli-public`
