# 이슈 003: Kakao Live RAG 시맨틱 검색 및 README 통합

**상태**: 열림
**생성일**: 2026-03-07

## 배경

패치된 `kakaocli` 저장소에는 이미 SQLite 메시지 저장소와 lexical 검색을 기반으로
한 로컬 Live RAG 파이프라인이 있다. 다음 단계는 현재의 로컬 중심 수집 및 서비스
흐름을 유지하면서 외부 임베딩 API 모델을 사용한 의미 기반 시맨틱 검색을 추가하는
것이다. 동시에 패치 저장소 안에는 `README.md`와 내용이 많이 겹치는 repo-local
`AGENTS.md` 파일이 남아 있는데, 워크스페이스 루트에는 이미 권위 있는 `AGENTS.md`
가 존재한다. 따라서 패치 저장소 문서는 하나의 명확한 사용 안내서로 통합되어야 한다.

## 완료 기준

- [ ] `kakaocli-patched/README.md`가 현재 `kakaocli-patched/AGENTS.md`에 있는
      repo-local 운영 안내를 직접 포함한다.
- [ ] `kakaocli-patched/AGENTS.md`가 제거되고, 이를 전제로 하는 문서 참조가 남지
      않는다.
- [ ] 기존 Live RAG 파이프라인이 현재 lexical 동작을 깨지 않으면서 `lexical`,
      `semantic`, `hybrid` 검색 모드를 지원한다.
- [ ] 시맨틱 검색은 외부 임베딩 API 모델을 사용하되, 검색 상태는 저장소 런타임
      데이터 디렉터리 아래 로컬에 유지된다.
- [ ] 검색 파이프라인 변경 부분은 실행 가능한 검증 명령과 안정 출력 slice에 대한
      MD5 비교로 확인된다.

## 작업 목록

- [ ] 1. `.agents/exceplan/` 아래에 이 작업용 영문/국문 ExecPlan 문서를 저장한다.
- [ ] 2. `kakaocli-patched/AGENTS.md` 내용을 `kakaocli-patched/README.md`로 통합한다.
- [ ] 3. 기존 `tools/live_rag` 파이프라인 위에 시맨틱 인덱싱과 검색을 추가한다.
- [ ] 4. 동작을 검증하고, 이슈/우회책 기록을 업데이트한 뒤, 요구된 한국어 커밋을 준비한다.

## 참고 사항

<!-- 작업 진행 중 결정 사항, 발견 사항, 차단 사항을 여기에 기록하세요 -->
