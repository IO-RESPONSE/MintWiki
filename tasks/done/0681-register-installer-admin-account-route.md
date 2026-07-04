# 0681 Register installer admin account route

## Goal

설치 마법사가 최초 관리자 계정을 생성하는 단계를 라우트로 등록한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Ui
- php/src/Modules
- php/tests

## Acceptance Criteria

- `GET /install/admin`이 `InstallAdminAccountFormPage`를 렌더하고 CSRF 토큰을 포함한다.
- `POST /install/admin`이 CSRF를 검증하고, 입력된 관리자 아이디/비밀번호로 관리자 계정 레코드를 `account` 테이블에 생성한다. 비밀번호는 해시(예: `password_hash`)로 저장한다.
- 계정+비밀번호 저장 컴포넌트가 없으면 이 태스크에서 최소한의 계정 생성 서비스를 추가한다. 범위가 커지면 확장하지 말고 후속 큐 태스크(0689+)로 분리한다.
- 비밀번호를 로그/응답에 노출하지 않는다.
- php 테스트로 폼 렌더, CSRF 거부, 관리자 생성(해시 저장)을 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- installer lock/완료 페이지 — 0682에서 수행.
- 일반 로그인/세션 흐름 — 0686.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 UI: `MintWiki\Ui\InstallAdminAccountFormPage`. `db/schema/account.sql` 스키마를 사용한다. User 모듈(`src/Modules/User`)은 현재 식별자 값 객체 위주이므로, 계정 영속화가 없으면 최소 Persistence를 추가한다.
