# 0677 Register installer welcome and requirements routes

## Goal

설치 마법사의 시작(welcome)과 환경 요구사항 점검 화면을 라우트로 등록해 브라우저에서 접근 가능하게 한다.

## Phase

Phase G: Front-Controller Live Wiring, 0673+.

## Scope

- php/public
- php/src/Ui
- php/tests/Http

## Acceptance Criteria

- `GET /install`이 `InstallWelcomePage`를 렌더한다.
- `GET /install/requirements`가 `RequirementCheck` 결과를 사용해 `InstallRequiredPage`(요구사항 점검) 화면을 렌더한다.
- 설치가 완료된 경우 이 라우트들은 `InstallerRouteGate`로 차단된다(0676 게이트 재사용).
- php 테스트로 각 라우트의 상태코드와 핵심 화면 요소를 검증한다.
- 기존 테스트가 계속 통과한다.

## Out of Scope

- DB 설정 폼 제출·config 기록 — 0678, 0679에서 수행.
- 스키마 적용·관리자 생성.
- 실제 라이브 배포.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존 UI 페이지 재사용: `MintWiki\Ui\InstallWelcomePage`, `MintWiki\Ui\InstallRequiredPage`. 요구사항 점검은 `MintWiki\Installer\RequirementCheck`를 사용한다. 동적 라우터(0675)는 여기서 필수는 아니지만 정적 경로로 등록한다.
