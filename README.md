# Codex Kakao Live RAG Wrapper

이 저장소는 `patched kakaocli + 저장형 semantic sidecar + launchd-backed Live RAG`를 묶어, Codex CLI가 카카오톡 질문에 로컬 근거 기반으로 답하도록 운영하는 래퍼 저장소입니다.

This repo is an operator-facing wrapper around the patched `kakaocli` workflow so Codex can answer KakaoTalk questions from local evidence instead of ad-hoc shell access.

## What This Repo Does

- 일상 질의 경로(day-to-day operator path)는 루트 래퍼 명령으로 고정합니다.
- 저수준 `kakaocli` 명령 카탈로그와 상세 설명은 [`kakaocli-patched/README.md`](kakaocli-patched/README.md)에서 확인합니다.
- 저장형 RAG는 `kakaocli-patched/.data/live_rag.sqlite3`에 유지됩니다.
- Live RAG는 `launchd`로 관리되어 `query-kakao` 호출 시 필요한 백그라운드 서비스가 자동 보장됩니다.

## Quick Start

### 1. Install

루트에서 아래 래퍼를 사용합니다.

```bash
./install-kakaocli
```

이 명령은 내부적으로 `kakaocli-patched`의 로컬 빌드와 `.venv` 런타임을 준비합니다.

### 2. Permissions and Status

macOS에서 최소 아래 확인이 필요합니다.

- Full Disk Access: 카카오톡 DB 읽기용
- Accessibility: UI 자동화가 필요한 명령용

상태 확인은 루트 래퍼로 시작합니다.

```bash
./kakaocli-local status
./kakaocli-local auth
./kakaocli-local login --status
```

## Evidence-Backed Queries

Codex가 카카오톡 관련 질문에 답할 때 기본 진입점(default entrypoint)은 `./query-kakao`입니다.

```bash
./query-kakao --json --query-text "박다훈 업데이트"
./query-kakao --json --mode lexical --query-text "업데이트"
./query-kakao --json --mode semantic --query-text "회의가 연기된 내용"
./query-kakao --json --mode hybrid --query-text "박다훈이 미룬 일정"
```

운영 규칙은 다음과 같습니다.

- 기본 질의 모드(default retrieval mode)는 `hybrid`입니다.
- semantic sidecar가 아직 없거나 사용할 수 없으면 lexical 결과로 fallback합니다.
- JSON 응답에는 필요 시 `requested_mode`와 `fallback_reason`가 포함되어 downgrade가 드러납니다.
- `./query-kakao`는 내부적으로 Live RAG 서비스 상태를 확인하고 필요하면 자동 기동합니다.

## Stored RAG and Semantic Sidecar

이 저장소의 canonical store는 다음 파일입니다.

```text
kakaocli-patched/.data/live_rag.sqlite3
```

구성은 다음처럼 나뉩니다.

- canonical messages: 정규화된 카카오 메시지 저장
- semantic sidecar: 같은 DB 안의 `semantic_chunks`와 runtime state
- retrieval service: canonical store와 semantic sidecar를 함께 사용

semantic build/update는 유지보수 경로(maintainer path)로만 실행합니다.

```bash
conda run -n module python kakaocli-patched/tools/live_rag/build_semantic_index.py --mode update

HF_TOKEN=hf_xxx conda run -n module python kakaocli-patched/tools/live_rag/build_semantic_index.py --mode rebuild --batch-size 20 --progress

HF_TOKEN=hf_xxx conda run -n module python kakaocli-patched/tools/live_rag/validate_semantic.py --use-temp-db
```

운영상 알아둘 점:

- semantic 검색은 Hugging Face 토큰이 있어야 합니다.
- semantic 후보는 현재 규칙상 `member_count <= 30` 채팅만 포함합니다.
- normal text message만 semantic 후보가 됩니다.
- embedding 규칙이나 semantic config signature가 바뀌면 `--mode rebuild`를 사용해야 합니다.
- canonical `messages`는 유지되고 semantic 데이터만 sidecar/runtime state로 관리됩니다.

## Live RAG Operations

Live RAG는 webhook app + sync follower를 `launchd`로 유지하는 구조입니다.

- LaunchAgent path: `~/Library/LaunchAgents/com.codex.kakaocli-live-rag.plist`
- service label: `com.codex.kakaocli-live-rag`
- operator path에서는 `/health`를 직접 두드리기보다 상태 명령을 사용합니다

상태 점검:

```bash
conda run -n module python kakaocli-patched/tools/live_rag/service_manager.py status
```

필요 시 유지보수자가 사용할 수 있는 관리 명령:

```bash
conda run -n module python kakaocli-patched/tools/live_rag/service_manager.py ensure
conda run -n module python kakaocli-patched/tools/live_rag/service_manager.py start
conda run -n module python kakaocli-patched/tools/live_rag/service_manager.py stop
```

현재 repo 로직 기준으로 `query-kakao`는 이 서비스가 내려가 있어도 자동 복구 경로를 통해 질의를 계속 시도합니다.

## Operator Path vs Maintainer Path

일반 운영(day-to-day operator):

- `./install-kakaocli`
- `./kakaocli-local status`
- `./kakaocli-local auth`
- `./query-kakao --json --query-text "..."`

유지보수(maintainer):

- `conda run -n module python kakaocli-patched/tools/live_rag/build_semantic_index.py ...`
- `conda run -n module python kakaocli-patched/tools/live_rag/validate_semantic.py --use-temp-db`
- `conda run -n module python kakaocli-patched/tools/live_rag/service_manager.py status`

주의:

- 이 repo의 기본 경로는 upstream/Homebrew `kakaocli`가 아닙니다.
- 루트 래퍼는 `kakaocli-patched` 내부 로컬 빌드와 런타임을 전제로 합니다.
- KakaoTalk 정보 조회나 요약은 먼저 `./query-kakao --json --query-text "<request>"`로 시작하는 것이 기준입니다.

## Low-Level Reference

저수준 명령 설명, raw `kakaocli` 기능, 설치 내부 동작이 더 필요하면 아래 문서를 봅니다.

- [`kakaocli-patched/README.md`](kakaocli-patched/README.md)

