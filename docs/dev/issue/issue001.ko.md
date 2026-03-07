# 이슈 001: Codex용 Kakao Live RAG 근거 계층 강화

**상태**: 완료
**생성일**: 2026-03-07

## 배경

현재 Kakao Live RAG 경로는 동작하지만, evidence contract가 얇고,
semantic 평가는 벤치마크되지 않았으며, 임베딩은 query와 document를
같게 처리하고, 배치 처리는 일부만 적용되어 있고, semantic coverage는
코드 안에 숨겨져 있습니다. 이 작업은 승인된 ExecPlan을 적용해서
Codex가 더 강한 근거 객체를 소비하게 하되, 기존 워크플로에서 기대하는
관찰 가능한 retrieval 결과는 안정적으로 유지하는 것을 목표로 합니다.

## 완료 기준

- [x] 결정론적 benchmark 명령이 MRR, NDCG, Precision@K, Recall@K를 출력한다.
- [x] `./query-kakao --json`이 matched chunk provenance를 포함한 안정적인 evidence contract를 반환한다.
- [x] query 임베딩과 document 임베딩이 모델 인지형 경로로 분리된다.
- [x] semantic index 빌드가 실제 embedding batch와 명시적 batch 제어를 사용한다.
- [x] chunking, semantic coverage, service mode가 숨은 기본값이 아니라 명시 정책이 된다.
- [x] 새 구현으로 legacy 기본 production 분기를 대체하되, 호환성이 필요한 기존 baseline 출력은 유지된다.

## 작업 목록

- [x] 1. 결정론적 fixture baseline과 benchmark/reference 출력을 고정한다.
- [x] 2. evidence contract와 retrieval payload 구성을 교체한다.
- [x] 3. 임베딩, 배치, chunking, semantic 정책 처리를 리팩터링한다.
- [x] 4. 새 service 동작을 명시 정책으로 만들고 기본값으로 적용한다.
- [x] 5. fixture benchmark, MD5 비교, 저장소 테스트 명령으로 검증한다.
- [x] 6. ExecPlan 진행 로그를 갱신하고 한국어 커밋 메시지로 마무리한다.

## 참고 사항

승인된 방향은 legacy 기본 경로의 하드 교체입니다. 복구나 비교 경로는
legacy production 경로를 되살리지 않는 범위에서만, 비기본 검증 또는
운영 안전장치로 남길 수 있습니다.

검증 요약:
- `conda run -n module python -m unittest discover -s tests -p 'test_*.py'` -> 테스트 `4`개 통과.
- `conda run -n module python kakaocli-patched/tools/live_rag/validate_semantic.py --use-temp-db --backend deterministic --validation all` -> snapshot MD5 `fb7059a13b81bfe358c51657ba3aadf0`, `matches_reference=true`.
