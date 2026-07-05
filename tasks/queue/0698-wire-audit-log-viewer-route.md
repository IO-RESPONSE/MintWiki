# 0698 Wire audit log viewer route

## Goal

감사 로그 뷰어 `GET /admin/audit` 라우트를 등록하고 0696 관리자 게이트로 보호하며, `audit_event` 테이블의 실제 이벤트를 `AuditViewerPage`/`AuditRow`로 렌더한다.

## Phase

Phase I: Admin console wiring, 0696+.

## Scope

- php/public/index.php
- php/src/Ui/AuditViewerPage.php, php/src/Ui/AuditRow.php (실데이터 주입)
- php/src/Modules/Audit 또는 조회 쿼리 (필요 시 read-only 조회기)
- php/tests

## Acceptance Criteria

- `GET /admin/audit`을 등록하고 관리자 게이트를 적용한다(익명 302/비관리자 403/관리자 통과).
- `audit_event` 테이블에서 최근 이벤트를 시간 내림차순으로 읽어 `AuditViewerPage`에 주입한다. 조회는 read-only이며 `RecentDocumentsQuery`(0693)처럼 단순 PDO 조회기 패턴을 따른다. 페이지 크기 상한(예: 최근 100건)을 둔다.
- 이벤트가 없을 때 빈 상태를 안전하게 렌더한다.
- 페이지는 스킨 `Layout` 안에서 렌더되고 모든 값은 `Escaper`로 이스케이프한다.
- php 테스트로 인가 3경로와, 주어진 이벤트 목록이 행으로 렌더되는지(및 빈 상태) 검증한다.

## Out of Scope

- 감사 이벤트 필터/검색 UI, CSV 내보내기.
- 감사 이벤트 쓰기(기록)는 기존 파이프라인 담당.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`AuditViewerPage(?Escaper, ?Layout)`·`AuditRow` 이미 존재. `db/schema/audit_event.sql`이 스키마 정본. 조회기는 도메인 프레임워크 없이 PDO 직접(코딩 표준 준수).
