# 외부 임베딩 기반 시맨틱 검색으로 Kakao Live RAG 확장

이 ExecPlan은 살아 있는 문서다. 작업이 진행되는 동안 `Progress`, `Surprises & Discoveries`, `Decision Log`, `Outcomes & Retrospective` 섹션을 계속 최신 상태로 유지해야 한다. 이 문서는 저장소 루트의 `.agents/PLANS.md` 규칙을 따라 유지해야 한다.

## 목적 / 큰 그림

이 변경이 끝나면 기존 Kakao Live RAG 흐름은 그대로 `kakaocli`를 통해 로컬에서 메시지를 수집하되, 검색이 더 이상 정확한 단어 일치에만 의존하지 않게 된다. 사용자는 채팅 원문과 질문 문장이 정확히 같지 않아도 “누가 회의를 미뤘다고 말한 메시지” 같은 의미 기반 질의를 할 수 있어야 한다. 눈으로 확인할 수 있는 결과는 기존 `tools/live_rag/query.py` 명령이 `semantic` 또는 `hybrid` 모드에서 의미 기반 검색 결과를 반환하고, 현재 lexical 검색도 그대로 동작하는 것이다. 같은 변경 안에서 문서 구조도 단순화해 `kakaocli-patched/README.md`를 저장소 내부의 단일 사용 안내서로 만들고, repo-local `AGENTS.md`는 퇴역시킨다.

## 진행 상황

- [x] (2026-03-07 05:54Z) 현재 검색 경로가 `kakaocli-patched/tools/live_rag/store.py`의 SQLite FTS와 `LIKE` fallback 기반임을 확인했다.
- [x] (2026-03-07 05:54Z) 기존 서비스 구조가 `backfill.py`와 `run_sync.py`의 수집, `app.py`의 HTTP 엔드포인트, `query.py`의 Codex용 CLI로 구성됨을 확인했다.
- [x] (2026-03-07 05:54Z) `kakaocli-patched/AGENTS.md`가 `kakaocli-patched/README.md`와 상당 부분 중복되고, 남은 고유 내용도 별도 agent rules 파일보다 README에 속하는 성격임을 확인했다.
- [x] (2026-03-07 06:03Z) `docs/issue/issue003.md`와 `docs/dev/issue/issue003.ko.md`에 영문/국문 추적 이슈 문서를 저장했다.
- [x] (2026-03-07 06:03Z) `.agents/exceplan/` 아래에 이 영문/국문 ExecPlan 문서를 저장했다.
- [x] (2026-03-07 06:24Z) 리뷰 지적사항을 반영해 두 ExecPlan을 함께 수정했고, 검증 경로를 재현 가능하게 만들고, AGENTS 퇴역 검사는 `kakaocli-patched/` 범위로 좁혔으며, 기록 대상도 현재 저장소에 실제로 존재하는 issue/progress 경로로 바꿨다.
- [x] (2026-03-07 07:25Z) repo-local `kakaocli-patched/AGENTS.md` 내용을 `kakaocli-patched/README.md`로 병합하고, 별도 repo-local AGENTS 파일을 전제하던 README 링크를 제거한 뒤 `kakaocli-patched/AGENTS.md`를 삭제했다.
- [x] (2026-03-07 07:25Z) 기존 `messages` 테이블을 읽어 텍스트를 chunk로 나누고, `huggingface_hub`를 통해 외부 임베딩 API를 호출하며, `.data/` 아래 Live RAG SQLite 안에 로컬 시맨틱 메타데이터를 저장하는 경로를 추가했다.
- [x] (2026-03-07 07:25Z) 기존 lexical fallback을 제거하지 않고 현재 서비스와 CLI에 `lexical`, `semantic`, `hybrid` 검색 모드를 노출했다.
- [x] (2026-03-07) 시맨틱 변경 후에도 런타임 경로가 유지됨을 확인했다. `conda run -n module python -m compileall tools/live_rag`, `./bin/install-kakaocli --build-only`, 서비스 재시작, `./bin/query-kakao --json --mode lexical --query-text "업데이트"`가 모두 성공했다.
- [x] (2026-03-07) 유효한 Hugging Face 토큰을 넣은 뒤 fixture 기반 임시 데이터베이스 semantic 검증이 통과함을 확인했다. `tools/live_rag/validate_semantic.py --use-temp-db`가 기대한 semantic hit 집합을 반환했다.
- [x] (2026-03-07) `Qwen/Qwen3-Embedding-8B` 응답이 `(1, 4096)` 형태로 올 때도 처리되도록 파서를 수정했다. 이전에는 이 payload가 비지원 형식으로 취급됐다.
- [x] (2026-03-07) 제한된 실데이터 semantic rebuild가 성공함을 확인했다. `tools/live_rag/build_semantic_index.py --mode rebuild --limit 20`이 완료되어 `.data/live_rag.sqlite3`에 sidecar 상태를 남겼다.
- [x] (2026-03-07) 최근 연구실 관련 채팅 subset을 임베딩해 “최근 연구실 사람들 간의 대화 주제가 뭐지?” 질문에 대해 의미 기반 hit를 반환하는 targeted semantic probe를 수행했다.
- [x] (2026-03-07) 배치 체크포인트와 진행률 출력을 추가했다. `build_semantic_index.py --mode update --limit 20 --batch-size 20 --progress`가 rebuild 체크포인트부터 이어서 실행되며 기존 chunk를 지우지 않고 `semantic_last_indexed_log_id`를 전진시켰다.
- [x] (2026-03-07) semantic 인덱싱 대상을 실제 텍스트 메시지로 좁히고, 임베딩 전에 대화방/보낸 사람/방향 메타데이터를 붙였다. 그 결과 교수님 지시사항 질문이 `semantic`/기본 `hybrid` 모드에서 교수 관련 대화 hit를 반환함을 확인했다.
- [x] (2026-03-07) operator-facing 기본 검색 동작을 `hybrid`로 정했고, semantic 상태를 사용할 수 없을 때 lexical fallback으로 안전하게 내려가도록 연결했다. JSON 응답에는 fallback 메타데이터를 남긴다.
- [x] (2026-03-07) 조용한 chat slice(`chat_id=421983255615844&limit=200`)에서 `/messages` MD5를 다시 확인했고, before/after 해시가 `9fdd299ebe49192b9a803f2f06ec9abb`로 일치했다.
- [x] (2026-03-07) `member_count > 30` 채팅방을 semantic 임베딩에서 제외하는 hard rule을 추가하고, `chat_metadata`를 로컬에 저장하며, metadata refresh가 불완전할 때 semantic build를 fail-closed로 중단하도록 만들었다.

## 놀라운 점과 발견 사항

- Observation: 저장소에는 이미 자동 재시작과 질의 라우팅을 갖춘 지속형 로컬 서비스가 있으므로, 시맨틱 검색을 넣어야 할 곳은 별도 mini-RAG가 아니라 현재 `tools/live_rag` 경로다.
  Evidence: `kakaocli-patched/tools/live_rag/query.py`는 `/retrieve`를 호출하기 전에 이미 서비스 실행을 보장한다.

- Observation: 현재 정답의 기준 원본은 임의 채팅 파일이 아니라 로컬 SQLite 데이터베이스다.
  Evidence: `kakaocli-patched/tools/live_rag/store.py`는 `messages`, FTS 상태, ingestion checkpoint 상태를 하나의 데이터베이스에 정의한다.

- Observation: 현재 Python 의존성 표면이 매우 작아서, 네이티브 의존성이 큰 계층이나 무거운 프레임워크를 추가하는 것은 이 저장소 성격과 맞지 않는다.
  Evidence: `kakaocli-patched/requirements-live-rag.txt`에는 현재 `fastapi`와 `uvicorn`만 있다.

- Observation: `kakaocli-patched/README.md`가 이미 운영 문서 대부분을 담고 있고, `kakaocli-patched/AGENTS.md`는 일부 repo-local 운영 세부사항을 더한 중복 문서에 가깝다.
  Evidence: 현재 README는 그 안내를 직접 담지 않고 여러 곳에서 `AGENTS.md`를 참조한다.

- Observation: 실제 운영자가 쓰는 wrapper 경로는 conda 환경을 직접 실행하지 않고, `kakaocli-patched/bin/query-kakao`가 repo-local `.venv`를 사용하며 `./bin/install-kakaocli`로 그 환경을 준비한다.
  Evidence: `kakaocli-patched/bin/query-kakao`는 `.venv/bin/python`을 `LIVE_RAG_PYTHON`으로 내보내고, `kakaocli-patched/bin/install-kakaocli`는 `requirements-live-rag.txt` 기준으로 그 환경을 다시 만든다.

- Observation: `huggingface_hub==1.1.0`의 `InferenceClient.feature_extraction`은 텍스트 목록 배치 입력이 아니라 단일 텍스트 호출 인터페이스를 노출한다.
  Evidence: 로컬 시그니처 점검 결과 `feature_extraction(self, text: str, ..., model: Optional[str] = None) -> np.ndarray` 형태였기 때문에, 문서 임베딩은 텍스트별 반복 호출로 구현해야 했다.

- Observation: 이 Mac의 현재 Hugging Face cached login은 존재하지만 임베딩용 inference provider 호출 권한이 없다.
  Evidence: `tools/live_rag/validate_semantic.py --use-temp-db`와 `tools/live_rag/build_semantic_index.py`가 `--embedding-provider hf-inference`를 주어도 `router.huggingface.co`에서 `403 Forbidden`을 반환했다.

- Observation: 전역 `/messages?limit=200` MD5는 구현 중 live ingestion 때문에 흔들렸지만, 조용한 chat 범위 slice는 안정적이었다.
  Evidence: 전역 export는 가장 최신/가장 오래된 `log_id`가 계속 바뀌었지만, `chat_id=421983255615844&limit=200`는 before/after 해시가 `9fdd299ebe49192b9a803f2f06ec9abb`로 일치했다.

- Observation: `--embedding-provider hf-inference`를 강제로 주는 방식은 이 환경에서 `Qwen/Qwen3-Embedding-8B`의 안정적인 경로가 아니었다.
  Evidence: 유효한 credential을 넣은 뒤에도 explicit `hf-inference` 호출은 `404`를 반환했고, 반면 기본 routed provider 경로는 임베딩을 정상 반환했다.

- Observation: 성공한 Qwen 임베딩 payload는 단일 텍스트인데도 평탄한 벡터가 아니라 2차원 배열로 도착했다.
  Evidence: `InferenceClient.feature_extraction(..., model="Qwen/Qwen3-Embedding-8B")` 직접 호출 결과가 `(1, 4096)` 형태였고, fixture 검증 통과 전에 파서 수정이 필요했다.

- Observation: 전체 rebuild가 끝나기 전에 작은 채팅 범위 semantic probe를 먼저 돌리는 것이 유용했다.
  Evidence: 최근 연구실 채팅만 따로 인덱싱했을 때는 “최근 연구실 사람들 간의 대화 주제가 뭐지?” 질문에 의미상 관련 있는 hit가 나왔지만, 오래된 row 몇 개만 담은 작은 전역 rebuild는 그렇지 않았다.

- Observation: system/feed row는 열린 기억형 질문에서 강한 semantic 노이즈였다.
  Evidence: 필터링 전에는 교수님 지시사항 질문의 상위 hit에 `feedType` JSON과 사진 placeholder가 섞였지만, 실제 텍스트 메시지만 인덱싱하고 메타데이터를 함께 임베딩한 뒤에는 같은 질문이 교수 관련 대화를 반환했다.

- Observation: `member_count`는 canonical Live RAG `messages` row에 저장되어 있지 않다.
  Evidence: 이 값은 `kakaocli chats --json`에서만 바로 얻을 수 있었기 때문에, semantic 필터링을 위해 별도의 `chat_metadata` 테이블과 build/update 전 refresh 단계가 필요했다.

## 결정 기록

- Decision: 첫 구현에서는 새로운 일반 transcript import 기능을 만들지 않고 기존 `kakaocli-patched/tools/live_rag` 파이프라인을 확장한다.
  Rationale: 저장소는 이미 Kakao 메시지를 지속형 SQLite 저장소로 정규화하고 있고 서비스도 동작하므로, 가장 안전한 방식은 그 단일 원본 위에 시맨틱 기능을 얹는 것이다.
  Date/Author: 2026-03-07 / Codex

- Decision: 외부 임베딩 API 개념은 유지하되, 저장과 검색은 로컬에 둔다.
  Rationale: 사용자는 시맨틱 검색을 위해 외부 임베딩을 원하지만, 저장소 스타일은 local-first이므로 벡터, 메타데이터, 랭킹은 저장소 런타임 상태 안의 디스크에 유지하는 편이 맞다.
  Date/Author: 2026-03-07 / Codex

- Decision: 성능 측정으로 필요성이 입증되기 전까지 첫 구현에서 FAISS를 필수로 두지 않는다.
  Rationale: 이 저장소는 이미 SQLite 기반이고 의존성이 작다. 첫 단계에서 로컬 저장 벡터와 NumPy cosine scoring만 사용하면 더 단순하고 디버깅이 쉬우며 현재 스타일과도 더 잘 맞는다. 이후 동일한 검색 인터페이스 뒤에서 FAISS로 옮길 여지는 남긴다.
  Date/Author: 2026-03-07 / Codex

- Decision: 현재 검색 경로를 대체하지 않고 lexical, semantic, hybrid 모드를 함께 제공한다.
  Rationale: 이것은 버그 수정이 아니라 기능 추가다. lexical 검색을 유지해야 정확한 이름이나 문구 검색을 보호하면서, 우회 표현을 찾는 semantic recall도 추가할 수 있다.
  Date/Author: 2026-03-07 / Codex

- Decision: `kakaocli-patched/AGENTS.md`는 퇴역시키고, 그 repo-local 운영 내용을 `kakaocli-patched/README.md`로 병합한다.
  Rationale: 루트 저장소에 이미 권위 있는 `AGENTS.md` 규칙 파일이 있다. `kakaocli-patched/` 안에 두 번째 repo-local `AGENTS.md`를 유지하면 구조적으로 혼란스럽고, 기존 README와도 중복되며, 사용자가 두 문서를 오가게 만든다.
  Date/Author: 2026-03-07 / Codex

- Decision: 임베딩 모델과 provider는 설정 가능하게 두되, 기본 타깃 모델은 `Qwen/Qwen3-Embedding-8B`로 한다.
  Rationale: Hugging Face routing과 provider 가용성은 계정과 모델 배포 상태에 따라 달라질 수 있으므로, 코드는 `HF_TOKEN` 또는 `hf auth login`을 받아들이고 필요하면 provider 이름도 선택 가능해야 한다. 특정 provider 문자열을 하드코딩하면 취약하다.
  Date/Author: 2026-03-07 / Codex

- Decision: 시맨틱 완료 기준은 결정적인 fixture 기반 검증 스크립트로 증명하고, 실제 Kakao 데이터베이스는 smoke check와 MD5 안정성 검증에만 사용한다.
  Rationale: 실제 Kakao 대화 이력은 머신마다 다르므로 고정된 실데이터 질의를 주 완료 기준으로 두면 재현 가능하지 않다. 임시 fixture 데이터베이스는 반복 가능한 증거를 주고, 실제 데이터베이스는 wrapper와 ingestion 경로가 계속 usable함을 보여준다.
  Date/Author: 2026-03-07 / Codex

- Decision: `rebuild` 시 기존 semantic sidecar 삭제는 임베딩 호출이 성공한 뒤로 미루고, semantic build/validation 진입점은 JSON 오류 payload를 출력한다.
  Rationale: Hugging Face 인증이 실패해도 기존 semantic 상태를 보존해야 하며, 운영자는 traceback보다 기계가 읽을 수 있는 실패 출력이 필요하다.
  Date/Author: 2026-03-07 / Codex

- Decision: `Qwen/Qwen3-Embedding-8B`에는 `hf-inference`를 강제하기보다 기본 Hugging Face routed provider 경로를 우선 사용한다.
  Rationale: 이 환경에서는 explicit `hf-inference`가 `404`를 반환했고, 반면 기본 provider routing은 토큰 권한과 billing이 맞을 때 유효한 임베딩을 반환했다.
  Date/Author: 2026-03-07 / Codex

- Decision: 전체 실데이터 rebuild가 느리거나 비싸더라도, 그 사이에는 targeted chat-scoped semantic probe를 중간 검증 방식으로 적극 활용한다.
  Rationale: fixture 데이터베이스가 semantic correctness를 증명해 주고, 최근 채팅 subset probe는 긴 전역 rebuild를 기다리지 않고도 사용자 체감 가치를 먼저 검증할 수 있다.
  Date/Author: 2026-03-07 / Codex

- Decision: `member_count > 30`을 저장소 차원의 semantic 임베딩 hard exclusion rule로 둔다.
  Rationale: 대형 그룹채팅은 semantic candidate 노이즈가 크고, semantic recall의 체감 가치는 direct/small-group 대화에서 더 높으며, 사용자가 이 기준을 상시 저장소 규칙으로 요청했다.
  Date/Author: 2026-03-07 / Codex

- Decision: operator-facing 기본값은 `hybrid`로 두고, semantic 상태를 사용할 수 없을 때만 lexical로 fallback한다.
  Rationale: 실제 질의 결과를 보면 열린 기억형 질문은 semantic recall의 이점을 크게 받았고, fallback을 lexical로 두면 sidecar가 아직 없거나 임베딩 호출이 실패하는 상황에서도 안전한 기본 동작을 유지할 수 있다.
  Date/Author: 2026-03-07 / Codex

## 결과와 회고

구현은 이제 들어가 있고, semantic 경로도 더 이상 이론 단계가 아니다. 패치 저장소는 `kakaocli-patched/README.md` 하나로 운영 가이드를 통합했고, 중복 repo-local `AGENTS.md` 파일은 제거했다. Live RAG 경로에는 semantic sidecar 빌드/갱신 스크립트와 서비스/CLI의 `lexical`, `semantic`, `hybrid` 검색 모드가 추가됐다. 관리형 서비스를 재시작한 뒤 lexical 동작은 여전히 wrapper를 통해 정상 동작했고, fixture 기반 semantic 검증도 `Qwen/Qwen3-Embedding-8B`로 통과한다. 이제 builder는 배치마다 체크포인트를 남기므로 긴 rebuild를 `--mode update`로 이어서 돌릴 수 있고, semantic build는 매번 `kakaocli chats --json`으로 `chat_metadata`를 갱신한 뒤 `member_count > 30` 채팅방을 semantic sidecar에서 제외한다. semantic config signature에는 embedding-rule version과 `max_member_count=30`도 함께 기록되므로, 규칙이 바뀌면 호환되지 않는 update가 아니라 rebuild가 필요하다는 점이 명시된다. 조용한 `/messages` slice에 대한 MD5 비교도 동일 해시로 닫혔다.

## 맥락과 구조 설명

여기서 말하는 구현 대상은 `kakaocli-patched/tools/live_rag` 아래에 있다. `store.py`는 현재 로컬 데이터베이스 계층이며, 정규화된 Kakao 메시지, 키워드 검색용 FTS 인덱스, 라이브 동기화 재개용 체크포인트를 저장한다. `app.py`는 `/health`, `/messages`, `/kakao`, `/retrieve` 엔드포인트를 제공한다. `query.py`는 백그라운드 서비스가 살아 있는지 확인한 뒤 검색 요청을 보내는 CLI 진입점이다. `backfill.py`는 과거 메시지를 `kakaocli`에서 불러오고, `run_sync.py`는 라이브 수집을 계속 진행한다.

사람이 읽는 운영 문서는 현재 패치 저장소 안에서 두 군데에 나뉘어 있다. `kakaocli-patched/README.md`와 `kakaocli-patched/AGENTS.md`다. 하지만 이 워크스페이스 전체의 실제 규칙 파일은 루트의 최상위 `AGENTS.md`다. 따라서 패치 저장소 안의 `AGENTS.md`는 두 번째 규칙 문서가 아니라 운영 설명 문서로 간주해야 한다. 이 계획에서는 그 운영 내용을 `README.md`로 합치고, repo-local `AGENTS.md` 파일은 삭제한다.

이 계획에서 “semantic retrieval”은 같은 단어가 아니라 비슷한 의미로 텍스트를 찾는 방식이다. “embedding”은 의미가 비슷한 문장끼리 가까운 위치에 놓이도록 모델이 만든 숫자 배열이다. “chunk”는 긴 대화 전체를 하나의 벡터로 만들지 않기 위해, 한 메시지 또는 짧은 메시지 묶음을 더 작은 검색 단위로 나눈 것이다. “hybrid retrieval”은 정확한 키워드 근거와 의미 유사도를 함께 사용해 하나의 정렬 결과를 만드는 방식이다.

첫 구현 범위에서는 의도적으로 일반 `.txt`, `.md`, `.json`, `.jsonl` 전사 파일 import를 넣지 않는다. 이 저장소는 이미 더 나은 메시지 원본을 가지고 있다. 바로 `live_rag.sqlite3` 안의 Kakao 메시지 행이다. 외부 전사 파일 import가 정말 필요해지면, 이 기능이 먼저 유용하다는 것이 검증된 뒤 별도 이슈로 다루는 편이 맞다.

사용자 진입점인 `/Users/alice/Documents/codex/query-kakao`는 `kakaocli-patched/bin/query-kakao`를 호출한다. 이 wrapper는 `module` conda 환경을 직접 쓰지 않고 패치 저장소의 `.venv`를 실행하며, 로컬 런타임이 없거나 오래되었으면 `./bin/install-kakaocli --build-only`를 통해 다시 준비한다. 따라서 `kakaocli-patched/requirements-live-rag.txt` 의존성 변경은 직접 `conda run -n module python ...`으로 디버깅하는 경로와, 운영자가 실제로 쓰는 wrapper 경로 양쪽 모두에서 검증해야 한다.

## 작업 계획

이 문서 앞부분에서 설명한 semantic 경로, README 통합, retrieval mode 연결은 이미 현재 워크트리에 구현되어 있다. 따라서 다음 세션은 처음부터 다시 만드는 구현 세션이 아니다. 이미 들어간 semantic 경로가 계속 건강한지 검증하고, 운영적으로 아직 약한 부분만 좁게 보완하고, 최종 operator-facing 동작을 기록하는 세션이다. 첫 번째 마일스톤은 semantic 경로를 “fixture와 subset에서는 증명됨” 상태에서 “실제 데이터베이스 전체에서도 실사용 가능” 상태로 끌어올리는 것이다. 먼저 현재 fixture 검증이 여전히 통과하는지 다시 확인하고, `.data/live_rag.sqlite3` 안의 semantic sidecar 통계를 읽어 현재 상태를 사실 기준으로 파악한다. 그 다음 현행 Qwen 설정으로 실데이터 전체 rebuild를 시도한다. rebuild가 적절한 시간 안에 끝나면 semantic count와 config signature를 기록하고 바로 operator-facing 질의 검증으로 넘어간다. 반대로 너무 오래 걸리면 막연히 다시 시작하지 말고, `build_semantic_index.py`에 resume 가능한 batching과 진행률 출력부터 추가해 긴 rebuild를 이어서 돌릴 수 있게 만든다.

두 번째 마일스톤은 operator-facing 기본 검색 동작을 결정하는 것이다. 현재 코드는 `lexical`, `semantic`, `hybrid`를 모두 지원하지만, 다음 세션에서는 “교수님이 나한테 지시하신 게 뭐지?” 같은 열린 기억형 질문에 대해 `query-kakao`가 무엇을 기본 동작으로 삼을지 명시적으로 정해야 한다. 선택지는 세 가지뿐이다. lexical을 기본값으로 유지하고 mode 전환을 명시적으로 요구하거나, 기본값을 hybrid로 바꾸거나, 정확한 문구 검색은 lexical로 유지하되 열린 기억형 질문에만 hybrid/semantic fallback을 태우는 좁은 규칙을 추가하는 방식이다. 이 결정은 취향이 아니라 실제 질의 결과를 근거로 내려야 한다.

세 번째 마일스톤은 실제 사용자 질문 형태로 semantic 검증을 마무리하는 것이다. 의미 있는 sidecar가 만들어지면 `tools/live_rag/query.py`와 `./bin/query-kakao` 양쪽에서 `semantic`과 `hybrid` 모드로 실제 운영자 질문 형태를 넣어 본다. 핵심 smoke test는 “교수님이 나한테 지시하신 게 뭐지?” 같은 질문이 의도한 교수 관련 대화에 근거한 hit를 반환하느냐이지, 임의의 오래된 메시지를 뽑느냐가 아니다. 결과가 약하면 원인을 semantic coverage 부족, chunking 규칙, recency filtering, rank 결합 방식 중 어디에 있는지 분해해서 봐야 한다.

네 번째 마일스톤은 정리와 증명이다. `/messages` MD5 비교는 반드시 고정되거나 조용한 slice를 고른 뒤 다시 수행해 ingestion drift가 비교를 오염시키지 않게 한다. 그 다음 `docs/issue/issue003.md`, `docs/dev/issue/issue003.ko.md`, 그리고 이 ExecPlan 두 파일에 최종 operator 동작, semantic build 상태, 장시간 rebuild를 위한 재사용 가능한 우회책이 무엇인지 기록한다.

## 구체적 단계

아래 명령은 별도 언급이 없으면 모두 `/Users/alice/Documents/codex/kakaocli-patched`에서 실행한다고 가정한다.

1. 더 건드리기 전에 semantic baseline이 여전히 살아 있는지 확인한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module python tools/live_rag/validate_semantic.py --use-temp-db

    예상 결과:
      fixture 기반 semantic 검증이 `{"status":"ok",...}`를 반환해 현재 토큰, 모델, 파서 경로가 여전히 정상임을 보여 준다.

2. 다음 세션 시작 시점의 semantic sidecar 상태를 먼저 읽는다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module python - <<'PY'
    from tools.live_rag.store import LiveRAGStore
    store = LiveRAGStore()
    print(store.semantic_stats())
    PY

    예상 결과:
      `.data/live_rag.sqlite3` 안에 현재 저장된 semantic chunk 수, message 수, config signature가 출력된다.

3. 현재 Qwen 설정으로 의미 있는 실데이터 전체 rebuild를 시도한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module python tools/live_rag/build_semantic_index.py --mode rebuild

    예상 결과:
      명령이 JSON 성공과 함께 충분히 큰 embedded chunk 수를 반환하거나, 남은 운영 문제의 핵심이 임베딩 정확성보다 rebuild 시간이라는 점을 분명히 보여 준다.

4. 전체 rebuild가 너무 느리거나 진행 상황이 안 보이면, 무작정 다시 시작하지 말고 builder 자체를 개선한다.

    편집 목표:
      `tools/live_rag/build_semantic_index.py`에 resume 가능한 batching과 진행률 출력을 넣고, 그 뒤 유용한 전체 sidecar가 생길 때까지 rebuild를 이어서 돌린다.

5. 관리형 서비스를 재시작하고 직접 경로와 wrapper 경로 둘 다에서 질의한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module python tools/live_rag/service_manager.py restart
    conda run -n module python tools/live_rag/query.py --mode semantic --json --query-text "교수님이 나한테 지시하신 게 뭐지?"
    conda run -n module python tools/live_rag/query.py --mode hybrid --json --query-text "교수님이 나한테 지시하신 게 뭐지?"
    ./bin/query-kakao --json --mode semantic --query-text "교수님이 나한테 지시하신 게 뭐지?"
    ./bin/query-kakao --json --mode hybrid --query-text "교수님이 나한테 지시하신 게 뭐지?"

    예상 결과:
      최소 한 가지 operator-facing 모드는 임의의 오래된 메시지가 아니라 의도한 교수 관련 대화에 근거한 hit를 반환해야 한다.

6. 실제 질의 결과를 본 뒤에만 기본 operator 동작을 결정한다.

    기록해야 할 결정:
      기본값을 `lexical`로 유지할지, `hybrid`로 바꿀지, 또는 열린 기억형 질문에만 좁은 fallback 규칙을 넣을지 정한다.

7. 고정되거나 조용한 메시지 slice에서 MD5를 다시 수행한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    curl -s http://127.0.0.1:8765/messages?limit=200 > /tmp/live_rag_messages_frozen_before.json
    md5 /tmp/live_rag_messages_frozen_before.json
    # canonical messages는 바꾸지 않고 semantic-sidecar 작업만 수행
    curl -s http://127.0.0.1:8765/messages?limit=200 > /tmp/live_rag_messages_frozen_after.json
    md5 /tmp/live_rag_messages_frozen_after.json

    예상 결과:
      정말 안정적인 slice라면 해시가 일치해야 하고, 다르면 semantic sidecar 회귀가 아니라 ingestion drift인지 설명할 수 있어야 한다.

8. issue 문서와 두 ExecPlan에 다음 세션의 최종 결과를 반영한다.

    cd /Users/alice/Documents/codex
    sed -n '1,160p' docs/issue/issue003.md
    sed -n '1,160p' docs/dev/issue/issue003.ko.md

    예상 결과:
      전체 semantic rebuild 완료 여부, 기본 검색 동작 결정, 교수님 질문 테스트 결과가 issue 문서와 이 ExecPlan 두 파일에 기록된다.

## 검증 및 완료 기준

이 변경은 동작으로 검증되어야 한다. 아래 조건이 모두 참일 때만 완료로 본다.

- 기존 lexical query 경로가 `tools/live_rag/query.py`를 통해 정확한 키워드 질의에 대해 계속 hit를 반환한다.
- `./bin/query-kakao --json --mode lexical --query-text "업데이트"`가 계속 동작해, semantic 변경 뒤에도 repo-local wrapper 경로가 정상임을 보여준다.
- `tools/live_rag/validate_semantic.py --use-temp-db`가 `Qwen/Qwen3-Embedding-8B` 기준 우회 표현 질의에 대해 기대한 fixture hit를 계속 반환한다.
- 실제 운영자의 현재 Kakao 이력에 대해 의미 있는 real-data semantic sidecar가 존재해야 한다. 이는 한 번의 전체 rebuild 성공이거나, 최소한 0부터 다시 시작하지 않고 끝까지 완료할 수 있는 resumable rebuild 경로여야 한다.
- “교수님이 나한테 지시하신 게 뭐지?” 질문에 대해 `semantic` 또는 `hybrid` 모드가 임의의 오래된 메시지가 아니라 의도한 교수 관련 대화에 근거한 hit를 반환해야 한다.
- `query-kakao`의 기본 operator-facing 검색 동작에 대해 명시적인 결정이 문서화되어 있어야 한다.
- 서비스가 재시작되어도 semantic sidecar 상태가 `.data/` 아래에 지속 저장되어 사라지지 않는다.
- 증분 인덱스 갱신은 새로 수집된 메시지 행만 처리하거나, 설정이 바뀌었을 때 안전하게 전체 재빌드를 수행한다.
- `/messages` 엔드포인트 출력은 semantic-sidecar 작업 전후 동일한 고정 또는 조용한 기준 slice에 대한 MD5 비교에서 안정적으로 유지된다.
- `kakaocli-patched/README.md`만 읽어도 설치, credential, lifecycle, Live RAG 라우팅, 로컬 agent/operator 주의점을 이해할 수 있으며, 두 번째 repo-local `AGENTS.md`를 보라고 하지 않는다.
- `kakaocli-patched/AGENTS.md`를 요구하는 참조가 남아 있지 않다.
- 문서가 `HF_TOKEN` 또는 기존 `hf auth login` 둘 중 하나로 Hugging Face 인증하는 방법을 설명한다.
- 요청 스키마와 CLI가 같은 명시적 recency 제어를 노출하고, lexical, semantic, hybrid 모두에서 일관되게 적용된다.
- 구현은 `conda run -n module python ...` 형태로 실행 가능하고, 새 벡터 데이터베이스나 UI를 요구하지 않는다.

## 반복 실행 안전성과 복구

이 계획은 여러 번 실행해도 안전해야 한다. `build_semantic_index.py --mode rebuild`를 다시 실행해도 semantic sidecar 데이터만 교체해야 하며, 정규 Kakao 메시지는 절대 지우면 안 된다. `--mode update`를 다시 실행하면 저장된 체크포인트나 chunk 서명을 기준으로 이미 인덱싱한 메시지를 건너뛰어야 한다. 임베딩 모델명, provider, chunk 규칙, 질의 템플릿이 바뀌면 semantic 쪽만 깨끗하게 다시 빌드하고 그 이유를 명확히 출력해야 한다. Hugging Face 인증이 실패하면 semantic 상태를 바꾸기 전에 중단하고, `HF_TOKEN`을 찾았는지 아니면 캐시된 로그인 자격증명을 찾았는지를 출력해야 한다. fixture 기반 `validate_semantic.py --use-temp-db` 경로는 자체 임시 데이터베이스를 만들고 정리해야 하며, 반복 실행으로 `.data/`를 오염시키면 안 된다. README 병합 단계도 여러 번 실행해도 안전해야 한다. 다시 실행해도 병합된 섹션이 중복되면 안 되며, repo-local `AGENTS.md` 삭제는 그 내용이 README에 안전하게 반영된 뒤에만 일어나야 한다.

## 산출물과 메모

구현이 끝나면 `kakaocli-patched/.data/` 아래에는 semantic 메타데이터, semantic 체크포인트 상태, 검색에 필요한 로컬 벡터 페이로드처럼 검사 가능한 산출물이 남아야 한다. 다만 검증에만 쓰인 임시 scratch 파일은 최종 정리 전에 삭제해야 한다. fixture 검증 경로가 `.data/` 밖에 임시 데이터베이스를 만들 수는 있지만, 그 파일도 자동으로 정리되어야 한다. 예시 출력은 현재 저장소 스타일에 맞게 짧고 JSON 중심으로 유지한다. 또한 사람 대상 문서 세트는 작업 전보다 단순해져야 한다. 패치 저장소에는 `README.md`만 남기고 중복된 repo-local `AGENTS.md`는 제거한다.

## 인터페이스와 의존성

기존 `kakaocli-patched/tools/live_rag` 모듈 경계를 유지한다. 아래 인터페이스들은 `Progress`에 기록된 완료 작업의 일부로 이미 저장소 안에 존재한다. 따라서 다음 세션에서는 이들을 새로 다시 구현할 대상으로 보지 말고, 남은 작업을 진행하는 동안 유지하고 검증해야 할 현재 계약으로 다룬다. 정말로 미완료된 운영 과제를 해결하는 데 필요할 때만 좁게 확장한다.

`kakaocli-patched/tools/live_rag/embedding_client.py`에는 이미 다음과 같은 안정적인 인터페이스를 가진 작은 클라이언트 래퍼가 있다.

    class ExternalEmbeddingClient:
        def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
        def embed_query(self, text: str) -> list[float]: ...

이 클라이언트는 이미 `HF_TOKEN` 또는 캐시된 로그인 상태의 Hugging Face 인증을 사용하고, 기본 모델은 `Qwen/Qwen3-Embedding-8B`이며, 선택적 provider override도 받는다. 다음 세션에서는 rebuild/default-mode 후속 작업을 진행하는 동안 이 동작이 계속 유지되는지 검증해야 한다.

`kakaocli-patched/tools/live_rag/store.py`에는 이미 다음 형태의 semantic-sidecar persistence 메서드가 들어가 있다.

    def iter_messages_for_embedding(self, after_log_id: int | None, limit: int | None) -> list[dict[str, Any]]: ...
    def upsert_semantic_chunks(self, chunks: list[dict[str, Any]]) -> dict[str, int]: ...
    def semantic_search(self, query_vector: list[float], limit: int, chat_id: int | None, speaker: str | None) -> list[dict[str, Any]]: ...

`kakaocli-patched/tools/live_rag/semantic_index.py`에는 이미 chunk 생성과 벡터 scoring helper가 있다. 현재 chunk 규칙은 단순하고 명시적이다. 짧은 Kakao 메시지는 메시지 1개를 chunk 1개로 사용하고, 긴 텍스트는 문자 수 기준으로 overlap을 두고 분할하되 `log_id`, `chat_id`, `sender`, `timestamp`, 원문 텍스트를 메타데이터에 유지한다. 남은 실데이터 검증에서 구체적인 검색 문제가 드러날 때만 이 규칙을 바꾼다.

`kakaocli-patched/tools/live_rag/app.py`에서는 `/retrieve`가 이미 다음 형태를 받는다.

    {
      "query": "...",
      "mode": "lexical" | "semantic" | "hybrid",
      "limit": 8,
      "semantic_top_k": 24,
      "chat_id": null,
      "speaker": null,
      "since_days": null,
      "context_before": 2,
      "context_after": 2
    }

`kakaocli-patched/tools/live_rag/query.py`에는 이미 다음 CLI 플래그가 있고, 서비스 요청 스키마와 계속 맞아야 한다.

    --mode lexical|semantic|hybrid
    --semantic-top-k N
    --since-days DAYS

`kakaocli-patched/tools/live_rag/build_semantic_index.py`는 이미 다음 옵션을 받는다.

    --mode rebuild|update
    --limit N
    --embedding-model MODEL_ID
    --embedding-provider PROVIDER
    --binary PATH
    --max-member-count N

`kakaocli-patched/tools/live_rag/validate_semantic.py`는 이미 임시 fixture 데이터베이스를 만들고, `LiveRAGStore.ingest_messages`를 통해 고정 메시지 세트를 넣고, semantic sidecar를 만든 뒤, 우회 표현 질의가 기대한 fixture `log_id`를 반환하는지 단정하는 진입점을 제공한다. 다음과 같은 안정적인 인터페이스는 계속 유지되어야 한다.

    conda run -n module python tools/live_rag/validate_semantic.py --use-temp-db

`kakaocli-patched/README.md`의 최종 내용은 현재 `kakaocli-patched/AGENTS.md`에만 분리되어 있던 로컬 운영 가이드를 이미 직접 포함하고 있다. 특히 다음 항목이 들어가 있어야 한다.
- credential 저장 동작
- 자동 로그인 및 lifecycle 동작
- 앱 상태 판별과 AX 관련 주의사항
- 로컬 Live RAG 라우팅과 예시
- troubleshooting 안내
- 전송 및 자동화 safety rules

`kakaocli-patched/requirements-live-rag.txt`에는 꼭 필요한 최소 패키지만 유지한다. 현재 예상 집합은 다음과 같다.

    fastapi
    uvicorn
    huggingface_hub
    numpy

LangChain은 넣지 않고, 외부 벡터 데이터베이스도 넣지 않으며, 두 번째 prompt/agent 프레임워크도 추가하지 않는다. 현재 서비스 표면이 이미 적절하기 때문이다.

## 변경 메모

이 개정된 ExecPlan은 앞서 논의된 “임의 채팅 파일 + HF 임베딩 + FAISS” 아이디어를 저장소 친화적으로 좁힌 버전이다. 외부 임베딩 개념은 유지하되, 원본 데이터는 기존 Kakao `messages` 저장소를 그대로 사용하고, lexical 검색은 유지하며, 첫 semantic 인덱스는 로컬에 단순하게 보관하는 방향으로 바꿨다. 여기에 문서 통합 요구사항도 명시적으로 추가했다. 루트 저장소가 실제 `AGENTS.md` 규칙 파일을 이미 가지고 있으므로, `kakaocli-patched/AGENTS.md`는 `kakaocli-patched/README.md`로 병합한 뒤 삭제한다.

변경 메모, 2026-03-07: 리뷰 이후 이 계획은 fixture 데이터베이스 기반의 재현 가능한 semantic 검증, 명시적인 before/after MD5 캡처, `kakaocli-patched/` 범위로 한정한 AGENTS 퇴역 검사, 그리고 현재 워크스페이스에 실제로 존재하는 issue/progress 경로를 가리키는 기록 절차를 추가하도록 보강되었다.

변경 메모, 2026-03-07 (handoff 갱신): 이제 `Qwen/Qwen3-Embedding-8B` 기반 semantic 가능성은 입증되었고, routed provider의 `(1, 4096)` 응답 shape도 파서가 처리한다. 제한된 실데이터 rebuild와 최근 연구실 채팅 subset semantic probe도 성공했다. 다음 세션은 전체 실데이터 coverage, operator-facing 기본 검색 동작, 교수님 지시사항 질문 흐름, 그리고 고정 데이터셋 MD5 검증에 집중해야 한다.

변경 메모, 2026-03-07 (상태 명확화 갱신): 남은 섹션들이 이제 현재 워크트리에 이미 존재하는 구현과, 아직 남아 있는 검증·운영 후속 작업을 구분해서 설명한다. 이미 들어간 semantic 인터페이스는 다시 새로 만들 대상이 아니라, 유지하고 검증해야 할 현재 계약으로 적었다.

변경 메모, 2026-03-07 (embedding rule 갱신): semantic 인덱싱은 이제 `kakaocli chats --json`에서 가져온 로컬 `chat_metadata` refresh에 의존하고, `member_count > 30` 채팅방을 제외하며, 그 규칙을 semantic config signature에 기록해 rebuild 요구 조건을 명시한다.
