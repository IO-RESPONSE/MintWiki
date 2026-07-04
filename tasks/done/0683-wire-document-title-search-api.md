# 0683 Wire document title search API

## Goal

홈 검색 폼이 호출하는 `GET /api/documents/by-title`를 Document 서비스에 연결해 제목으로 문서를 조회한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Modules/Document
- php/tests/Http

## Acceptance Criteria

- `GET /api/documents/by-title?q=...`가 `Document\Service`(+ `DocumentRepository`, PDO)를 사용해 제목으로 문서를 조회한다.
- 찾으면 문서 정보를 JSON으로 반환하고, 없으면 404 JSON을 반환한다.
- DB 미설정 시에는 명확한 오류(예: 503/JSON)로 응답하고 앱이 죽지 않는다.
- 제목 정규화는 기존 `Document\Title`을 사용한다.
- php 테스트로 조회 성공/미존재/미설정 경로를 검증한다(리포지토리 주입 또는 InMemoryRepository 사용).
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 전문(full-text) 검색 — Search 모듈은 별도 후속 작업.
- 문서 보기/편집 UI — 0684, 0685.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트: `MintWiki\Modules\Document\Service`, `DocumentRepository`(PDO 연동), `InMemoryRepository`(테스트용), `Title`. Search 모듈(`src/Modules/Search`)은 현재 비어 있으므로 여기서는 제목 조회로 한정한다.
