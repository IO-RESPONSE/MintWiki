# 0715 Document delete

## Goal

문서 삭제 기능을 구현한다 — 삭제 서비스/저장소, 라우트, 권한/CSRF/확인, 삭제 버튼 UI, 감사 이벤트 기록. 현재는 삭제 수단이 전혀 없다.

## Phase

Phase K: Delete + audit logging + backup download, 0714+.

## Scope

- php/src/Modules/Document (Repository/Service delete)
- php/src/Modules/Acl/DefaultPolicy (delete 기본 정책)
- php/public/index.php (삭제 라우트)
- php/src/Ui (삭제 버튼 + 확인)
- php/tests

## Acceptance Criteria

- `Document\Repository`/`Service`에 문서 삭제를 추가한다. 리비전·토론 등 FK 종속을 안전하게 처리한다(하드 삭제 시 관련 리비전/스레드 정리 또는 소프트 삭제 중 하나를 택하고 근거를 남긴다). SQLite/MariaDB 양쪽 이식성 유지.
- `POST /wiki/{title}/delete`를 등록한다 — `CsrfTokenService` 검증(실패 403), 삭제 권한 확인, 성공 시 홈(또는 삭제 안내)로 302. 위험 동작이므로 확인 단계(체크박스/확인 토큰, 기존 `AdminDangerConfirmation` 참고)를 거친다.
- 권한: `Permission::Delete`로 판정한다. `DefaultPolicy`에 delete 기본 규칙을 추가한다 — 익명 deny + 로그인 사용자 allow(edit/discuss와 동일 패턴, first-match 순서 유지). 문서별 acl_rule이 있으면 그것이 우선.
- `DocumentActionTabs` 또는 문서 보기 화면에 로그인·권한 있는 사용자에게만 "삭제" 버튼/링크를 노출한다(익명·무권한에는 숨김). 모든 출력 `Escaper` 이스케이프.
- 삭제 시 감사 이벤트를 기록한다(0714 `PdoAuditRecorder` 사용).
- php 테스트로 (1) 삭제 서비스/저장소 동작 + FK 정리, (2) 라우트의 CSRF·권한(익명 302/무권한 403)·확인 누락 거부·정상 삭제 후 302, (3) 삭제 버튼 노출 조건, (4) 감사 이벤트 기록을 검증한다.

## Out of Scope

- 삭제 복구(휴지통)·일괄 삭제 — 후속.
- 리비전 단위 삭제.

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`Permission::Delete` case 이미 존재. `DefaultPolicy`는 최근 discuss 기본규칙 추가와 동일 방식으로 delete 규칙을 더한다(익명 deny + ALL allow). 감사 기록은 0714에 의존. 확인 UI는 `AdminDangerConfirmation` 재사용 가능.
