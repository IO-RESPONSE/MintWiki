# 0699 Wire report list and user block routes

## Goal

신고 목록 `GET /admin/reports`와 사용자 차단 `GET /admin/users/block` + `POST /admin/users/block` 라우트를 등록하고 0696 관리자 게이트로 보호하며, CSRF로 상태 변경 요청을 보호한다.

## Phase

Phase I: Admin console wiring, 0696+.

## Scope

- php/public/index.php
- php/src/Ui/AdminReportListPage.php, php/src/Ui/BlockUserFormPage.php
- php/src/Modules/User 또는 차단 처리기
- php/tests

## Acceptance Criteria

- `GET /admin/reports`(AdminReportListPage), `GET /admin/users/block`(BlockUserFormPage 폼), `POST /admin/users/block`(차단 처리)을 등록하고 세 라우트 모두 관리자 게이트를 적용한다.
- `POST /admin/users/block`은 기존 `CsrfTokenService`로 토큰을 검증하고(실패 시 403), 대상 사용자를 차단하며, 완료 후 폼/목록으로 302 리다이렉트한다. 유효성 오류는 `render(array $errors)`로 폼에 다시 표시한다.
- 신고 목록·차단 폼은 스킨 `Layout` 안에서 렌더되고 모든 값은 `Escaper`로 이스케이프한다.
- 차단은 기존 사용자 모델/저장소를 사용하고 데이터 계층에 필요한 최소 변경만 한다(도메인 프레임워크 도입 금지).
- php 테스트로 인가 3경로, CSRF 누락/불일치 거부, 정상 차단 후 리다이렉트, 폼 오류 재표시를 검증한다.

## Out of Scope

- 차단 해제 UI, 차단 사유 정책, 알림.
- 신고 접수(사용자측) 흐름.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`AdminReportListPage(?Escaper, ?Layout)`, `BlockUserFormPage(...)` + `render(array $errors=[])` 이미 존재. CSRF는 install/login POST에서 쓰는 `Security\CsrfTokenService` 재사용. 차단 상태 저장 컬럼/테이블이 없으면 최소 스키마를 추가하되 기존 스키마 정책(portable timestamp/collation)을 따른다.
