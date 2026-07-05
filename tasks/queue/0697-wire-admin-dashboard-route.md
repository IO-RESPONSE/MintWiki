# 0697 Wire admin dashboard route

## Goal

관리자 콘솔 진입점인 `GET /admin` 라우트를 프론트 컨트롤러에 등록하고, 0696의 관리자 게이트로 보호하며, 기존 `AdminDashboardPage`를 나무위키 스킨(`Layout`)에 통합해 출력한다.

## Phase

Phase I: Admin console wiring, 0696+.

## Scope

- php/public/index.php
- php/src/Ui/AdminDashboardPage.php (필요 시 Layout/스킨 통합)
- php/tests/Http, php/tests/Ui

## Acceptance Criteria

- `GET /admin`을 등록하고 0696 관리자 게이트를 먼저 적용한다 — 비로그인 302(`/login`), 비관리자 403, 관리자만 대시보드 렌더.
- `AdminDashboardPage`가 Phase H 스킨(상단바/사이드바가 있는 `Layout`) 안에서 렌더되도록 통합한다(다른 페이지와 동일한 헤더/푸터).
- 대시보드는 관리 하위 화면(감사 로그, 신고, 사용자 차단, 유지보수, 백업/복원, 진단)으로 가는 링크 목록을 보여준다 — 링크 대상 경로는 0698–0702에서 등록할 경로와 일치시킨다.
- 모든 출력은 기존 `Escaper`로 이스케이프한다.
- php 테스트로 (1) 익명/비관리자/관리자 접근 결과, (2) 대시보드에 하위 화면 링크와 스킨 마크업이 포함되는지 검증한다.

## Out of Scope

- 하위 화면 자체의 라우트(0698–0702).
- 대시보드 실데이터 위젯(통계 수치 등) — 링크 허브로 충분.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`AdminDashboardPage(?Escaper, ?Layout)` 이미 존재·테스트됨. index.php 라우트 등록 관례는 기존 `$router->register('GET', '/wiki/{title}', ...)`와 동일. 게이트는 0696 산출물을 사용.
