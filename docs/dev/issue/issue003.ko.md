# 이슈 003: Kakao Live RAG 시맨틱 검색 및 README 통합

**상태**: 완료
**생성일**: 2026-03-07

## 배경

패치된 `kakaocli` 저장소에는 이미 SQLite 메시지 저장소와 lexical 검색을 기반으로
한 로컬 Live RAG 파이프라인이 있다. 다음 단계는 현재의 로컬 중심 수집 및 서비스
흐름을 유지하면서 외부 임베딩 API 모델을 사용한 의미 기반 시맨틱 검색을 추가하는
것이다. 동시에 패치 저장소 안에는 `README.md`와 내용이 많이 겹치는 repo-local
`AGENTS.md` 파일이 남아 있는데, 워크스페이스 루트에는 이미 권위 있는 `AGENTS.md`
가 존재한다. 따라서 패치 저장소 문서는 하나의 명확한 사용 안내서로 통합되어야 한다.

## 완료 기준

- [x] `kakaocli-patched/README.md`가 현재 `kakaocli-patched/AGENTS.md`에 있는
      repo-local 운영 안내를 직접 포함한다.
- [x] `kakaocli-patched/AGENTS.md`가 제거되고, 이를 전제로 하는 문서 참조가 남지
      않는다.
- [x] 기존 Live RAG 파이프라인이 현재 lexical 동작을 깨지 않으면서 `lexical`,
      `semantic`, `hybrid` 검색 모드를 지원한다.
- [x] 시맨틱 검색은 외부 임베딩 API 모델을 사용하되, 검색 상태는 저장소 런타임
      데이터 디렉터리 아래 로컬에 유지된다.
- [x] 검색 파이프라인 변경 부분은 실행 가능한 검증 명령과 안정 출력 slice에 대한
      MD5 비교로 확인된다.

## 작업 목록

- [x] 1. `.agents/exceplan/` 아래에 이 작업용 영문/국문 ExecPlan 문서를 저장한다.
- [x] 2. `kakaocli-patched/AGENTS.md` 내용을 `kakaocli-patched/README.md`로 통합한다.
- [x] 3. 기존 `tools/live_rag` 파이프라인 위에 시맨틱 인덱싱과 검색을 추가한다.
- [x] 4. 동작을 검증하고, 이슈/우회책 기록을 업데이트한 뒤, 요구된 한국어 커밋을 준비한다.

## 참고 사항

- `kakaocli-patched/tools/live_rag/` 아래에 `embedding_client.py`,
  `semantic_index.py`, `build_semantic_index.py`, `validate_semantic.py`를 추가해
  semantic sidecar 구축 경로를 구현했다.
- `app.py`, `query.py`, `store.py`를 확장해서 `/retrieve`와 CLI가 `lexical`,
  `semantic`, `hybrid` 모드와 공통 `since_days` 필터를 처리하도록 바꿨다.
- `requirements-live-rag.txt`, `bin/install-kakaocli`, `bin/query-kakao`를 함께
  수정해 conda 개발 경로와 repo-local `.venv` wrapper 경로가 모두
  `huggingface_hub`, `numpy`를 포함하도록 맞췄다.
- 관리형 서비스를 재시작한 뒤 lexical smoke check는 통과했다. wrapper 응답은
  기존 hit 집합을 유지하면서 top-level `"mode": "lexical"` 필드를 추가한다.
- 현재 Mac의 Hugging Face cached login은 inference provider 호출 권한이 없어
  `validate_semantic.py --use-temp-db`와 `build_semantic_index.py`가
  `403 Forbidden`으로 실패한다. 두 스크립트는 이제 traceback 대신 JSON 오류를 출력한다.
- `/messages?limit=200` MD5는 구현 중 live sync가 새 Kakao row를 계속 받아서
  변경됐다. canonical endpoint의 스키마는 유지되지만, 안정적인 MD5 증명을 위해서는
  조용한 데이터셋이나 고정된 스냅샷이 필요하다.
- semantic builder는 이제 배치마다 체크포인트를 기록하므로
  `--mode update --batch-size N --progress`로 이어서 빌드할 수 있고,
  긴 rebuild도 0부터 다시 시작할 필요가 없다.
- semantic 임베딩 입력은 이제 일반 텍스트 메시지만 대상으로 삼고,
  임베딩 전에 대화방/보낸 사람/방향 메타데이터를 함께 붙여서 열린 기억형 질문의
  실데이터 검색 품질을 높였다.
- semantic build는 이제 인덱싱 전에 `kakaocli chats --json`으로
  `chat_metadata`를 새로 받아 로컬 Live RAG DB에 저장하고, candidate row에 대한
  metadata가 불완전하면 semantic sidecar를 건드리기 전에 fail-closed로 중단한다.
- 현재 임베딩 규칙은 `member_count > 30` 채팅방을 semantic sidecar에서 제외한다.
  이런 대형 그룹채팅은 lexical 검색에서는 계속 보이지만, semantic chunk나 hybrid의
  semantic-sidecar hit에는 들어가지 않는다.
- semantic config signature에는 이제 embedding-rule version과
  `max_member_count=30`이 포함되므로, 규칙이 바뀌면 호환되지 않는 update 대신
  rebuild를 강제한다.
- operator-facing 기본값은 이제 `hybrid`다. semantic sidecar를 아직 만들지
  않았거나 사용할 수 없을 때는 lexical 결과로 자동 fallback하고,
  JSON 응답에 `requested_mode`와 `fallback_reason`을 남긴다.
- 새 chunk 형식으로 sidecar를 다시 쌓은 뒤
  `tools/live_rag/query.py --json --query-text "교수님이 나한테 지시하신 게 뭐지?"`
  와 `./bin/query-kakao --json --query-text "교수님이 나한테 지시하신 게 뭐지?"`
  모두 교수 관련 대화에 근거한 hit를 반환했다.
- fixture semantic validator도 이제 chat metadata를 함께 넣어 새 fail-closed
  임베딩 규칙을 자동 검증 경로에서 함께 확인한다.
- 조용한 `/messages` slice에 대한 MD5도 안정적으로 맞았다.
  `chat_id=421983255615844&limit=200` 기준 before/after 해시는
  `9fdd299ebe49192b9a803f2f06ec9abb`로 동일했다.
