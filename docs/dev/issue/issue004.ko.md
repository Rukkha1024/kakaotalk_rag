# 이슈 004: 현재 Live RAG 로직에 맞춰 embedding rules 문서 동기화

**상태**: 완료
**생성일**: 2026-03-07

## 배경

workspace에는 semantic embedding 및 validation 작업의 기준이 되는
`.agents/embedding-rules.md` 파일이 있습니다. Live RAG semantic pipeline이
변경된 뒤 이 문서가 실제 필터 로직, metadata fail-closed 동작, semantic config
signature 규칙과 어긋나게 되었고, 현재 구현은 `kakaocli-patched/tools/live_rag/`
아래 코드가 authoritative source 입니다.

## 완료 기준

- [x] `.agents/embedding-rules.md`가 현재 semantic candidate filter 로직과 일치한다.
- [x] 문서가 builder가 사용하는 local chat metadata 및 semantic runtime state
      테이블을 명시한다.
- [x] 문서가 semantic text 구성과 config-signature rebuild 규칙을 설명한다.
- [x] 갱신된 문서가 `kakaocli-patched/README.md`와 충돌하지 않는다.

## 작업 목록

- [x] 1. 현재 rules 문서를 `semantic_index.py`, `build_semantic_index.py`,
         `store.py`와 대조한다.
- [x] 2. 기존의 짧은 section 스타일을 유지하면서 `.agents/embedding-rules.md`를 갱신한다.
- [x] 3. diff가 documentation-only 변경인지, operator 문서와 일치하는지 확인한다.
- [x] 4. 요구된 한국어 커밋 메시지로 커밋한다.

## 참고 사항

- 이번 작업은 repository guidance만 갱신하며 public API나 runtime logic은 변경하지 않는다.
- 검증은 semantic pipeline 출력 MD5가 아니라 source cross-check와 diff inspection으로 수행한다.
