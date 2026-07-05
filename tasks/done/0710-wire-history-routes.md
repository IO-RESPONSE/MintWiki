# 0710 Wire document history and diff routes

## Goal

문서 역사(history) 라우트를 배선해 액션 탭의 "역사"가 실제로 동작하게 한다 — 리비전 목록과 리비전 간 diff를 보여준다.

## Phase

Phase J: NamuMark rendering + edit UX + history/discussion, 0704+.

## Scope

- php/public/index.php (history/diff 라우트)
- php/src/Ui/DocumentHistoryPage.php, php/src/Ui/DocumentDiffPage.php (데이터 주입)
- php/tests

## Acceptance Criteria

- `GET /wiki/{title}/history`를 등록한다 — `Revision\PdoRepository.listByDocumentId()`로 해당 문서의 리비전을 시간 내림차순으로 읽어 `DocumentHistoryPage`에 주입한다. 각 행에 작성자·시각·편집 요약(0707)·해당 리비전 보기/비교 링크를 보여준다.
- `GET /wiki/{title}/diff?from={revId}&to={revId}`(경로/쿼리 형태는 기존 관례에 맞게)를 등록한다 — 두 리비전 source의 차이를 `DocumentDiffPage`로 보여준다.
- 두 라우트 모두 ACL read 권한을 적용한다(기존 `/wiki/{title}` 읽기 정책과 동일). 존재하지 않는 문서/리비전은 안전한 404/오류 처리.
- 액션 탭의 "역사" 링크(`/wiki/{title}/history`)가 이제 200으로 동작한다. 리비전이 없거나 1개일 때 빈/단일 상태를 안전하게 렌더.
- 모든 출력은 `Escaper`로 이스케이프하고 스킨 `Layout` 안에서 렌더한다.
- php 테스트로 (1) history 라우트가 리비전 목록을 렌더, (2) diff 라우트가 두 리비전 비교를 렌더, (3) ACL 거부, (4) 빈/단일 리비전 경계를 검증한다.

## Out of Scope

- 리비전 되돌리기(revert)·롤백 — 후속.
- 리비전별 렌더 diff(문법 렌더 기준 비교) — 우선 source 기준 diff.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`DocumentHistoryPage`·`DocumentDiffPage` 컴포넌트와 `Revision\PdoRepository`(create/get/listByDocumentId) 모두 존재. 라우트만 미배선이라 404였음. diff 알고리즘은 기존 diff 유틸이 있으면 재사용, 없으면 라인 단위 최소 구현.
