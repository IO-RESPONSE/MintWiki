# 0700 Wire maintenance mode routes

## Goal

유지보수 모드 관리 화면 `GET /admin/maintenance`와 토글 `POST /admin/maintenance` 라우트를 등록하고 0696 관리자 게이트 + CSRF로 보호하며, 유지보수 상태를 지속화해 프론트 컨트롤러가 이를 반영하게 한다.

## Phase

Phase I: Admin console wiring, 0696+.

## Scope

- php/public/index.php
- php/src/Ui/MaintenanceModePage.php
- php/src/Modules (유지보수 상태 저장/조회)
- php/tests

## Acceptance Criteria

- `GET /admin/maintenance`(현재 상태 + 토글 폼)와 `POST /admin/maintenance`(켜기/끄기)를 등록하고 관리자 게이트를 적용한다.
- `POST`는 `CsrfTokenService`로 검증(실패 시 403)하고 유지보수 상태를 지속화(예: 설정 파일 또는 전용 테이블/설정 행)한 뒤 302로 돌아온다.
- 유지보수 모드가 켜져 있으면 관리자가 아닌 일반 요청에 대해 프론트 컨트롤러가 유지보수 안내(`MaintenanceModePage` 또는 503)를 보여준다. **관리자와 `/login`·`/health`·`/admin/*`은 유지보수 중에도 접근 가능**해야 관리자가 모드를 해제할 수 있다.
- 페이지는 스킨 `Layout` 안에서 렌더되고 값은 `Escaper`로 이스케이프한다.
- php 테스트로 인가 3경로, CSRF 거부, 토글 지속화, 유지보수 ON일 때 일반 요청 차단 + 관리자/로그인/헬스 예외를 검증한다.

## Out of Scope

- 예약 유지보수(스케줄), 사용자 대상 공지 배너.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`MaintenanceModePage(?Escaper, ?Layout)` 이미 존재. 상태 지속화는 DB 연결 전에도 읽혀야 하므로(유지보수 중 DB 문제 대비) 설정 파일 기반이 안전하나, 기존 `ConfigLoader`/설정 관례에 맞춰 선택한다. 프론트 컨트롤러 반영은 `InstallerRouteGate`가 개입하는 지점과 유사한 위치에 배치.
