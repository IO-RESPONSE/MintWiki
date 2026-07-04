# 0685 Add document create and edit routes

## Goal

문서를 생성·편집하고 저장 시 새 리비전을 남기는 라우트를 추가한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Ui
- php/src/Modules/Document
- php/src/Modules/Revision
- php/tests/Http

## Acceptance Criteria

- `GET /wiki/{title}/edit`가 편집 폼(제목·본문, CSRF 토큰)을 렌더한다. 문서가 없으면 새 문서 작성 폼으로 동작한다.
- `POST /wiki/{title}/edit`(또는 동등 액션)이 CSRF를 검증하고, `Document\Service`로 문서를 생성/갱신하며 `Revision` 모듈로 새 리비전을 기록한다.
- 저장 성공 시 문서 보기(`/wiki/{title}`)로 리다이렉트한다.
- 빈 제목/본문 등 검증 오류는 폼으로 되돌려 표시한다.
- php 테스트로 신규 생성, 기존 편집(리비전 증가), CSRF 거부, 검증 오류를 확인한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 인증/권한 적용 — 0686, 0687에서 수행.
- 삭제/이력 UI.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 컴포넌트: `MintWiki\Modules\Document\Service`, `MintWiki\Modules\Revision\RevisionRepository`, `MintWiki\Security\CsrfTokenService`. 문서-리비전 연결은 기존 create-first-revision 로직(태스크 0029 참조)을 따른다.
