# Codex Kakao Operator Docs

이 저장소는 제품 코드 저장소가 아니라, Codex가 KakaoTalk 관련 작업을 수행할 때
따라야 하는 운영자용 지침 문서 모음입니다.

## 목적

- `AGENTS.md`에 전역 작업 규칙을 둡니다.
- `.agents/` 아래에 Kakao 작업과 일반 작업용 스킬 문서를 둡니다.
- `progress/` 아래에 작업 기록을 남깁니다.

공개용 `kakaocli` 제품 코드는 이 저장소에 포함되지 않습니다.

## Kakao 작업 원칙

- Kakao 정보 조회는 먼저 `query-kakao --json --query-text "<request>"`를 사용합니다.
- 설치, 권한, 로그인, 상태 확인, 저수준 진단은 `kakaocli` 명령으로 처리합니다.
- `query-kakao` 또는 `kakaocli`가 없으면, 외부 toolkit 설치가 먼저 필요합니다.
- 다른 사람에게 메시지를 보내는 작업은 항상 명시적 사용자 확인이 필요합니다.

## 로컬 보존 항목

- `.env`: embedding API 등 로컬 환경 설정
- `.data`: chat history / RAG 데이터

이 두 디렉터리/파일은 문서 저장소와 별도로 로컬 런타임 데이터로 유지합니다.
