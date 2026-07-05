# 0714 PDO audit recorder and mutation wiring

## Goal

감사 로그가 실제로 쌓이도록 `audit_event`에 기록하는 PDO 기반 `AuditRecorder` 구현체를 만들고, 주요 변경 동작(문서 생성/편집, 로그인/로그아웃)이 이벤트를 기록하도록 프론트 컨트롤러에 연결한다. 현재는 `NoOpAuditRecorder`뿐이라 `/admin/audit` 뷰어가 항상 비어 있다.

## Phase

Phase K: Delete + audit logging + backup download, 0714+.

## Scope

- php/src/Modules/Audit (PdoAuditRecorder)
- php/public/index.php (recorder 주입 + 변경 동작에서 record 호출)
- php/tests

## Acceptance Criteria

- `PdoAuditRecorder implements AuditRecorder`를 추가한다 — `record(AuditEvent $event)`가 `audit_event` 테이블에 INSERT한다. 스키마(`db/schema/audit_event.sql`)의 컬럼에 매핑하고, 기존 `Revision\PdoRepository` 관례(명시적 컬럼, 이식성 정책)를 따른다.
- `index.php`에서 `$pdo`가 연결된 경우 `PdoAuditRecorder`를, 아니면 `NoOpAuditRecorder`를 주입한다(DB 미설정 시에도 죽지 않게).
- 최소 다음 동작이 이벤트를 기록한다: 문서 생성, 문서 편집(리비전 생성), 로그인 성공, 로그아웃. 각 이벤트는 module/action/대상 식별자/행위자(계정 id 또는 anonymous)/시각을 담는다. 기록 실패가 사용자 요청을 깨뜨리지 않도록 방어적으로 처리한다.
- `/admin/audit` 뷰어가 이제 기록된 이벤트를 시간 내림차순으로 보여준다(0698 `RecentAuditEventsQuery` 재사용).
- php 테스트로 (1) `PdoAuditRecorder`가 이벤트를 저장·조회, (2) 문서 생성/편집·로그인 경로가 이벤트를 남기는지, (3) recorder가 없거나 실패해도 주 동작이 성공하는지 검증한다.

## Out of Scope

- 삭제 이벤트 기록(0715에서 삭제 구현과 함께).
- 감사 이벤트 필터/검색 UI.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

기존: `Modules/Audit/{AuditEvent,AuditEventRecord,AuditRecorder,NoOpAuditRecorder,RecentAuditEventsQuery}`, `Http/DocumentCreateHandler`가 이미 `AuditRecorder->record()`를 호출하는 예시. 도메인 프레임워크 금지(0424) — Recorder는 PDO 직접. `MintWiki\Audit` 네임스페이스.
