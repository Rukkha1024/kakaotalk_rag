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
- [ ] 검증은 일부만 완료됐다 (완료: 의존성 설치, wrapper 재빌드, lexical smoke test, 서비스 재시작, AGENTS 퇴역 grep, JSON 형태의 semantic 실패 검증; 남음: inference provider 권한이 있는 토큰으로 semantic build/query 성공 확인, 그리고 live sync가 중간에 slice를 바꾸지 않는 조용한 데이터셋에서 MD5 재확인).

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

- Observation: `/messages?limit=200` MD5가 전후 스냅샷에서 달라진 이유는 구현 중에도 live ingestion이 계속 진행됐기 때문이다.
  Evidence: 두 export 모두 200개 항목을 유지했지만, 가장 최신/가장 오래된 `log_id`가 바뀌어 응답 스키마 회귀가 아니라 수집 드리프트임을 보여 줬다.

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

## 결과와 회고

구현은 이제 들어가 있다. 패치 저장소는 `kakaocli-patched/README.md` 하나로 운영 가이드를 통합했고, 중복 repo-local `AGENTS.md` 파일은 제거했다. Live RAG 경로에는 semantic sidecar 빌드/갱신 스크립트와 서비스/CLI의 `lexical`, `semantic`, `hybrid` 검색 모드가 추가됐다. 관리형 서비스를 재시작한 뒤 lexical 동작은 여전히 wrapper를 통해 정상 동작했다. 남은 공백은 코드 자체가 아니라 환경 증명이다. 이 Mac의 Hugging Face cached credential은 현재 inference provider 권한이 없어서 결정적인 semantic validation과 실제 semantic index build가 차단되어 있다. 또한 MD5 비교는 구현 중 live sync가 새 row를 계속 받아 왔기 때문에, 조용하거나 고정된 데이터셋에서 다시 수행해야 한다.

## 맥락과 구조 설명

여기서 말하는 구현 대상은 `kakaocli-patched/tools/live_rag` 아래에 있다. `store.py`는 현재 로컬 데이터베이스 계층이며, 정규화된 Kakao 메시지, 키워드 검색용 FTS 인덱스, 라이브 동기화 재개용 체크포인트를 저장한다. `app.py`는 `/health`, `/messages`, `/kakao`, `/retrieve` 엔드포인트를 제공한다. `query.py`는 백그라운드 서비스가 살아 있는지 확인한 뒤 검색 요청을 보내는 CLI 진입점이다. `backfill.py`는 과거 메시지를 `kakaocli`에서 불러오고, `run_sync.py`는 라이브 수집을 계속 진행한다.

사람이 읽는 운영 문서는 현재 패치 저장소 안에서 두 군데에 나뉘어 있다. `kakaocli-patched/README.md`와 `kakaocli-patched/AGENTS.md`다. 하지만 이 워크스페이스 전체의 실제 규칙 파일은 루트의 최상위 `AGENTS.md`다. 따라서 패치 저장소 안의 `AGENTS.md`는 두 번째 규칙 문서가 아니라 운영 설명 문서로 간주해야 한다. 이 계획에서는 그 운영 내용을 `README.md`로 합치고, repo-local `AGENTS.md` 파일은 삭제한다.

이 계획에서 “semantic retrieval”은 같은 단어가 아니라 비슷한 의미로 텍스트를 찾는 방식이다. “embedding”은 의미가 비슷한 문장끼리 가까운 위치에 놓이도록 모델이 만든 숫자 배열이다. “chunk”는 긴 대화 전체를 하나의 벡터로 만들지 않기 위해, 한 메시지 또는 짧은 메시지 묶음을 더 작은 검색 단위로 나눈 것이다. “hybrid retrieval”은 정확한 키워드 근거와 의미 유사도를 함께 사용해 하나의 정렬 결과를 만드는 방식이다.

첫 구현 범위에서는 의도적으로 일반 `.txt`, `.md`, `.json`, `.jsonl` 전사 파일 import를 넣지 않는다. 이 저장소는 이미 더 나은 메시지 원본을 가지고 있다. 바로 `live_rag.sqlite3` 안의 Kakao 메시지 행이다. 외부 전사 파일 import가 정말 필요해지면, 이 기능이 먼저 유용하다는 것이 검증된 뒤 별도 이슈로 다루는 편이 맞다.

사용자 진입점인 `/Users/alice/Documents/codex/query-kakao`는 `kakaocli-patched/bin/query-kakao`를 호출한다. 이 wrapper는 `module` conda 환경을 직접 쓰지 않고 패치 저장소의 `.venv`를 실행하며, 로컬 런타임이 없거나 오래되었으면 `./bin/install-kakaocli --build-only`를 통해 다시 준비한다. 따라서 `kakaocli-patched/requirements-live-rag.txt` 의존성 변경은 직접 `conda run -n module python ...`으로 디버깅하는 경로와, 운영자가 실제로 쓰는 wrapper 경로 양쪽 모두에서 검증해야 한다.

## 작업 계획

첫 번째 마일스톤은 동작 변경 전에 문서를 통합하는 것이다. `kakaocli-patched/README.md`를 업데이트해 현재 `kakaocli-patched/AGENTS.md`에 흩어져 있는 repo-local 운영 정보를 직접 포함시킨다. 여기에는 credential 저장 방식, 자동 lifecycle 관리, 앱 상태 판별, AX 특이사항, Live RAG 라우팅, troubleshooting, safety rules가 포함된다. 그리고 README 안에서 “자세한 내용은 AGENTS.md를 보라”는 링크를 제거한다. README가 이 내용을 완전히 담게 되면 `kakaocli-patched/AGENTS.md`를 삭제한다. 이 작업은 단순한 문서 미화가 아니다. 이미 상위 저장소에 진짜 `AGENTS.md`가 있는 환경에서, 오해를 부르는 두 번째 `AGENTS.md` 파일을 제거하는 구조 정리다.

두 번째 마일스톤은 현재 수집 경로를 건드리지 않는 로컬 시맨틱 인덱스 빌더다. Hugging Face 임베딩 호출을 감싸는 `kakaocli-patched/tools/live_rag/embedding_client.py`를 추가한다. 이 모듈은 환경 변수 `HF_TOKEN` 또는 `hf auth login`으로 캐시된 토큰 둘 중 하나를 사용해야 하며, 문서 임베딩과 질의 임베딩을 각각 생성하는 메서드를 제공해야 한다. 그리고 `kakaocli-patched/tools/live_rag/semantic_index.py`를 추가해 chunk 분할, 벡터 직렬화, cosine similarity 점수 계산, 인덱스 상태 관리를 담당하게 한다. `kakaocli-patched/tools/live_rag/store.py`는 같은 SQLite 데이터베이스 안에 chunk 메타데이터, 모델 식별자, 임베딩 체크포인트 상태를 저장할 수 있도록 확장한다. 기존 메시지 행은 그대로 두고, semantic 관련 데이터만 sidecar로 붙인다.

세 번째 마일스톤은 현재 동작을 유지하는 검색 API다. `kakaocli-patched/tools/live_rag/app.py`의 `/retrieve`가 `lexical`, `semantic`, `hybrid` 세 값을 받는 `mode` 필드를 처리하도록 확장한다. 기존 lexical 구현은 안전한 기본 경로로 유지한다. semantic 검색 경로는 들어온 질의를 임베딩하고, 로컬 chunk 점수를 계산한 뒤, 일치한 chunk를 다시 주변 Kakao 메시지 문맥으로 확장해서 현재 `query.py`가 기대하는 것과 같은 응답 형태를 반환해야 한다. hybrid 경로는 lexical 결과 목록과 semantic 결과 목록을 서로 다른 점수 체계에 덜 민감한 간단한 순위 결합 방식으로 합친다. 응답 형식은 여전히 LLM 프롬프트에 바로 주입하기 쉬워야 한다. 현재 저장소가 retrieval을 그 방식으로 사용하기 때문이다.

네 번째 마일스톤은 운영성과 안전성이다. `kakaocli-patched/tools/live_rag/query.py`에 `--mode`, `--semantic-top-k`, `--since-days`를 추가해 recency 필터가 암묵적 가정이 아니라 명시적 인터페이스가 되게 한다. 기존 메시지 저장소를 기준으로 전체 재생성 또는 증분 갱신을 수행할 수 있는 새 스크립트 `kakaocli-patched/tools/live_rag/build_semantic_index.py`를 추가하고, 이 스크립트가 설정 가능한 임베딩 모델과 provider를 받게 한다. `kakaocli-patched/requirements-live-rag.txt`에는 가장 작은 실용 의존성 집합만 넣는데, 예상 후보는 `huggingface_hub`와 `numpy`이며 더 큰 프레임워크는 피한다. 또한 `kakaocli-patched/README.md`를 업데이트해 이후 운영자가 `module` conda 환경에서 토큰 설정, 모델 선택, lexical과 semantic 검색 차이, 실행 명령을 바로 이해할 수 있게 한다. `./bin/query-kakao`는 repo-local `.venv`를 쓰므로, 이 마일스톤에서는 `./bin/install-kakaocli`와의 호환성도 함께 유지해 wrapper가 의존성 변경 뒤에도 계속 동작해야 한다.

다섯 번째 마일스톤은 검증과 저장소 정리다. 예를 들어 `kakaocli-patched/tools/live_rag/validate_semantic.py` 같은 작은 검증 스크립트를 추가해, 임시 격리 데이터베이스를 만들고, 고정된 Kakao 스타일 fixture 메시지를 주입하고, 문서 임베딩 호출 1회 성공과 로컬 인덱스 빌드 1회 성공을 증명하고, 우회 표현 질의 1회가 기대한 fixture hit를 반환한다는 것을 증명한다. 실제 Live RAG 데이터베이스에 대한 별도 smoke check는 lexical 동작과 wrapper 사용성 확인용으로 유지하되, 고정된 실데이터 semantic 질의를 주 완료 기준으로 삼지는 않는다. semantic 기능 추가 전에 안정적인 `/messages` 엔드포인트 export를 먼저 저장하고, 변경 후 다시 저장해 MD5를 비교함으로써 정규 수집 출력은 변하지 않았음을 증명한다. README 통합이 끝난 뒤에는 `kakaocli-patched/` 범위 안에서만 검색을 실행해 `kakaocli-patched/AGENTS.md`에 대한 참조가 남아 있지 않음을 확인한다. 구현 메모와 차단 사항은 `docs/issue/issue003.md`와 `docs/dev/issue/issue003.ko.md`에 남기고, 별도 보존할 가치가 있는 반복 가능한 환경 해결책이 생기면 `kakaocli-patched/progress/` 아래에 타임스탬프 Markdown 노트를 추가한다. 임시 산출물은 지운 뒤, 구현 검토와 승인 이후에만 요구된 한국어 git commit을 만든다.

## 구체적 단계

아래 명령은 별도 언급이 없으면 모두 `/Users/alice/Documents/codex/kakaocli-patched`에서 실행한다고 가정한다.

1. 코드 변경 전에 추적 문서를 만든다.

    cd /Users/alice/Documents/codex
    ls docs/issue | sort
    ls docs/dev/issue | sort

2. 시맨틱 코드 변경 전에 패치 저장소 문서를 통합한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    rg -n "AGENTS.md" README.md AGENTS.md

    예상 결과:
      README.md에 제거해야 할 기존 링크가 보인다.
      이 시점에는 AGENTS.md가 아직 존재하며, 병합 후 삭제된다.

3. 지정된 conda 환경 안에서 Python 의존성을 설치하거나 갱신한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    conda run -n module pip install -r requirements-live-rag.txt

4. 검색 코드를 건드리기 전에 repo-local wrapper 런타임을 새로 맞추고, 현재 로컬 서비스가 동작하는지 확인하며, 기준 출력을 먼저 저장한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    ./bin/install-kakaocli --build-only
    conda run -n module python tools/live_rag/service_manager.py ensure
    curl -s http://127.0.0.1:8765/messages?limit=200 > /tmp/live_rag_messages_before.json
    md5 /tmp/live_rag_messages_before.json
    ./bin/query-kakao --json --query-text "업데이트"

    예상 성공 형태:
      {"query":"업데이트","hits":[...]}
    auth가 깨졌을 때 예상 실패 형태:
      Failed to query live RAG: ...

5. 기존 Kakao 메시지에서 semantic sidecar를 빌드하거나 갱신한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    HF_TOKEN=... conda run -n module python tools/live_rag/build_semantic_index.py --mode rebuild --limit 500

    예상 성공 형태:
      {"status":"ok","embedded_chunks":500,"updated_from_log_id":12345,"model":"Qwen/Qwen3-Embedding-8B"}

6. 결정적인 fixture 데이터베이스를 사용해 semantic 검증 스크립트를 실행한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    HF_TOKEN=... conda run -n module python tools/live_rag/validate_semantic.py --use-temp-db

    예상 성공 형태:
      {"status":"ok","fixture_query":"회의 연기된 내용","expected_log_id":123,"semantic_hit_log_ids":[123,...]}
    Hugging Face 인증이 없을 때 예상 실패 형태:
      {"status":"error","stage":"embed_documents","message":"..."}

7. fixture 검증이 통과한 뒤, 실제 로컬 데이터베이스에 대해서는 semantic/hybrid를 smoke check로만 확인한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    HF_TOKEN=... conda run -n module python tools/live_rag/query.py --mode semantic --json --query-text "<실제 메시지의 우회 표현>"
    HF_TOKEN=... conda run -n module python tools/live_rag/query.py --mode hybrid --json --query-text "<같은 우회 표현>"

    예상 결과:
      명령은 `"mode":"semantic"` 및 `"mode":"hybrid"`가 포함된 JSON을 반환한다.
      hit 개수는 로컬 Kakao 이력에 따라 달라질 수 있으므로, 이 단계는 주 semantic 증명이 아니라 smoke check다.

8. 안정 출력 slice를 저장하고 전후 MD5를 비교한다.

    cd /Users/alice/Documents/codex/kakaocli-patched
    curl -s http://127.0.0.1:8765/messages?limit=200 > /tmp/live_rag_messages_after.json
    md5 /tmp/live_rag_messages_before.json
    md5 /tmp/live_rag_messages_after.json

    예상 결과:
      정규 메시지 출력이 바뀌지 않았다면 MD5 해시가 일치한다.
      일치하지 않으면 정렬, 포맷, 의도치 않은 ingestion drift 중 무엇이 원인인지 설명하고 멈춘다.

9. repo-local AGENTS 파일이 완전히 퇴역했는지 확인한다.

    cd /Users/alice/Documents/codex
    rg -n "kakaocli-patched/AGENTS.md|\\[AGENTS\\.md\\]\\(AGENTS\\.md\\)|See \\[AGENTS\\.md\\]" /Users/alice/Documents/codex/kakaocli-patched

    예상 결과:
      `kakaocli-patched/README.md`나 다른 패치 저장소 문서 안에 삭제된 repo-local AGENTS 파일을 요구하는 참조가 남아 있지 않다.

10. 이미 존재하는 추적 이슈 문서에 구현 메모를 반영한다.

    cd /Users/alice/Documents/codex
    sed -n '1,120p' docs/issue/issue003.md
    sed -n '1,120p' docs/dev/issue/issue003.ko.md

    예상 결과:
      구현 메모, 차단 사항, 최종 검증 요약을 두 issue 파일에 기록한다.
      별도 우회책 노트가 필요하면 `kakaocli-patched/progress/YYMMDD-HHMM-*.md` 형태로 추가한다.

## 검증 및 완료 기준

이 변경은 동작으로 검증되어야 한다. 아래 조건이 모두 참일 때만 완료로 본다.

- 기존 lexical query 경로가 `tools/live_rag/query.py`를 통해 정확한 키워드 질의에 대해 계속 hit를 반환한다.
- `./bin/query-kakao --json --query-text "업데이트"`가 의존성 및 검색 변경 뒤에도 계속 동작해, repo-local wrapper 경로가 정상임을 보여준다.
- `tools/live_rag/validate_semantic.py --use-temp-db`가 우회 표현 질의에 대해 기대한 fixture hit를 `semantic` 모드에서 반환한다.
- `hybrid` 모드는 현재 검색 경로와 같은 응답 스키마로 병합 결과 목록을 반환한다.
- 서비스가 재시작되어도 semantic sidecar 상태가 `.data/` 아래에 지속 저장되어 사라지지 않는다.
- 증분 인덱스 갱신은 새로 수집된 메시지 행만 처리하거나, 설정이 바뀌었을 때 안전하게 전체 재빌드를 수행한다.
- `/messages` 엔드포인트 출력은 semantic 작업 전후 동일한 기준 slice에 대한 MD5 비교에서 안정적으로 유지된다.
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

기존 `kakaocli-patched/tools/live_rag` 모듈 경계를 유지한다.

`kakaocli-patched/tools/live_rag/embedding_client.py`에는 다음과 같은 안정적인 인터페이스를 가진 작은 클라이언트 래퍼를 정의한다.

    class ExternalEmbeddingClient:
        def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
        def embed_query(self, text: str) -> list[float]: ...

이 클라이언트는 `HF_TOKEN` 또는 캐시된 로그인 상태의 Hugging Face 인증을 사용해야 하며, 기본 모델은 `Qwen/Qwen3-Embedding-8B`로 하고 선택적 provider override를 받아야 한다.

`kakaocli-patched/tools/live_rag/store.py`에는 다음 형태의 semantic-sidecar persistence 메서드를 추가한다.

    def iter_messages_for_embedding(self, after_log_id: int | None, limit: int | None) -> list[dict[str, Any]]: ...
    def upsert_semantic_chunks(self, chunks: list[dict[str, Any]]) -> dict[str, int]: ...
    def semantic_search(self, query_vector: list[float], limit: int, chat_id: int | None, speaker: str | None) -> list[dict[str, Any]]: ...

`kakaocli-patched/tools/live_rag/semantic_index.py`에는 chunk 생성과 벡터 scoring helper를 정의한다. chunk 규칙은 단순하고 명시적으로 둔다. 짧은 Kakao 메시지는 메시지 1개를 chunk 1개로 사용하고, 긴 텍스트는 문자 수 기준으로 overlap을 두고 분할하되 `log_id`, `chat_id`, `sender`, `timestamp`, 원문 텍스트를 메타데이터에 유지한다.

`kakaocli-patched/tools/live_rag/app.py`에서는 `/retrieve`가 다음 형태를 받도록 확장한다.

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

`kakaocli-patched/tools/live_rag/query.py`에는 다음 CLI 플래그를 추가한다.

    --mode lexical|semantic|hybrid
    --semantic-top-k N
    --since-days DAYS

`kakaocli-patched/tools/live_rag/build_semantic_index.py`는 다음 옵션을 받아야 한다.

    --mode rebuild|update
    --limit N
    --embedding-model MODEL_ID
    --embedding-provider PROVIDER

`kakaocli-patched/tools/live_rag/validate_semantic.py`는 임시 fixture 데이터베이스를 만들고, `LiveRAGStore.ingest_messages`를 통해 고정 메시지 세트를 넣고, semantic sidecar를 만든 뒤, 우회 표현 질의가 기대한 fixture `log_id`를 반환하는지 단정하는 진입점을 제공해야 한다. 다음과 같은 안정적인 인터페이스면 충분하다.

    conda run -n module python tools/live_rag/validate_semantic.py --use-temp-db

`kakaocli-patched/README.md`의 최종 내용은 현재 `kakaocli-patched/AGENTS.md`에만 분리되어 있는 로컬 운영 가이드를 직접 포함해야 한다. 특히 다음 항목이 포함되어야 한다.
- credential 저장 동작
- 자동 로그인 및 lifecycle 동작
- 앱 상태 판별과 AX 관련 주의사항
- 로컬 Live RAG 라우팅과 예시
- troubleshooting 안내
- 전송 및 자동화 safety rules

`kakaocli-patched/requirements-live-rag.txt`에는 꼭 필요한 최소 패키지만 추가한다. 현재 예상 집합은 다음과 같다.

    fastapi
    uvicorn
    huggingface_hub
    numpy

LangChain은 넣지 않고, 외부 벡터 데이터베이스도 넣지 않으며, 두 번째 prompt/agent 프레임워크도 추가하지 않는다. 현재 서비스 표면이 이미 적절하기 때문이다.

## 변경 메모

이 개정된 ExecPlan은 앞서 논의된 “임의 채팅 파일 + HF 임베딩 + FAISS” 아이디어를 저장소 친화적으로 좁힌 버전이다. 외부 임베딩 개념은 유지하되, 원본 데이터는 기존 Kakao `messages` 저장소를 그대로 사용하고, lexical 검색은 유지하며, 첫 semantic 인덱스는 로컬에 단순하게 보관하는 방향으로 바꿨다. 여기에 문서 통합 요구사항도 명시적으로 추가했다. 루트 저장소가 실제 `AGENTS.md` 규칙 파일을 이미 가지고 있으므로, `kakaocli-patched/AGENTS.md`는 `kakaocli-patched/README.md`로 병합한 뒤 삭제한다.

변경 메모, 2026-03-07: 리뷰 이후 이 계획은 fixture 데이터베이스 기반의 재현 가능한 semantic 검증, 명시적인 before/after MD5 캡처, `kakaocli-patched/` 범위로 한정한 AGENTS 퇴역 검사, 그리고 현재 워크스페이스에 실제로 존재하는 issue/progress 경로를 가리키는 기록 절차를 추가하도록 보강되었다.
