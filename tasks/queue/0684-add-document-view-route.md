# 0684 Add document view route

## Goal

제목으로 문서를 조회해 HTML로 보여주는 `GET /wiki/{title}` 라우트를 추가한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Ui
- php/src/Modules/Document
- php/tests/Http

## Acceptance Criteria

- 동적 라우터(0675)를 사용해 `GET /wiki/{title}`를 등록한다.
- `Document\Service`로 문서를 조회해, 현재 리비전 본문을 HTML로 렌더한다(기존 `Layout` 재사용).
- 문서가 없으면 "문서 없음 + 만들기 링크"를 담은 404 HTML을 반환한다.
- 본문 렌더는 기존 Parser/Render 모듈이 있으면 사용하고, 없으면 안전하게 escape한 평문으로 표시한다.
- php 테스트로 존재/미존재 경로와 제목 파라미터 추출을 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 편집/저장 — 0685에서 수행.
- ACL 적용 — 0687.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트: `MintWiki\Modules\Document\Service`, `MintWiki\Ui\Layout`, 그리고 `src/Modules/Parser`·`src/Modules/Render`(사용 가능 시). 현재 리비전 조회는 `Revision` 모듈(`RevisionRepository`)을 참고한다.
