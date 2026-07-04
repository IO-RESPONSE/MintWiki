# 0678 Register installer database form route

## Goal

설치 마법사의 데이터베이스 설정 입력 폼 화면을 라우트로 등록한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Ui
- php/tests/Http

## Acceptance Criteria

- `GET /install/database`가 `InstallDBFormPage`를 렌더한다.
- 폼은 host/port/dbname/user/password 입력 필드를 포함하고, `CsrfTokenService`로 CSRF 토큰을 심는다.
- 설치 완료 시 `InstallerRouteGate`로 차단된다.
- php 테스트로 폼 라우트 상태코드, 필드 존재, CSRF 토큰 포함을 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- 폼 제출 처리 및 config 파일 기록 — 0679에서 수행.
- 스키마 적용.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 UI: `MintWiki\Ui\InstallDBFormPage`, 보안: `MintWiki\Security\CsrfTokenService`. 제출 대상 액션은 `POST /install/database`(0679)로 둔다.
