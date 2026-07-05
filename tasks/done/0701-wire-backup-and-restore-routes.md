# 0701 Wire backup and restore routes

## Goal

백업 `GET /admin/backup` + `POST /admin/backup`와 복원 `GET /admin/restore` + `POST /admin/restore` 라우트를 등록하고 0696 관리자 게이트 + CSRF + 위험작업 확인(`AdminDangerConfirmation`)으로 보호한다.

## Phase

Phase I: Admin console wiring, 0696+.

## Scope

- php/public/index.php
- php/src/Ui/BackupPage.php, php/src/Ui/RestorePage.php, php/src/Ui/AdminDangerConfirmation.php
- php/src/Modules (백업/복원 실행기, 이미 있으면 재사용)
- php/tests

## Acceptance Criteria

- `GET /admin/backup`(백업 목록/생성 폼), `POST /admin/backup`(백업 생성), `GET /admin/restore`(복원 폼), `POST /admin/restore`(복원 실행)을 등록하고 모두 관리자 게이트를 적용한다.
- 상태 변경 POST 두 개는 `CsrfTokenService`로 검증(실패 시 403)한다. 복원은 파괴적이므로 `AdminDangerConfirmation`으로 명시적 확인 단계를 거친다(확인 토큰/체크박스 없으면 실행 거부).
- 처리 결과(성공/오류)를 사용자에게 표시하고, `RestorePage::render(array $errors)`로 오류를 재표시한다.
- 페이지는 스킨 `Layout` 안에서 렌더되고 값은 `Escaper`로 이스케이프한다.
- php 테스트로 인가 3경로, CSRF 거부, 복원 확인 누락 시 거부, 정상 흐름을 검증한다. 실제 파일시스템 파괴가 없도록 테스트는 실행기를 주입/모의한다.

## Out of Scope

- 백업 스케줄링, 원격 스토리지 업로드.
- 공유호스팅 실서버에서의 실제 백업 아티팩트 경로 확정(운영 런북에서 다룸).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`BackupPage(?Escaper, ?Layout)`, `RestorePage(...)` + `render(array $errors=[])`, `AdminDangerConfirmation` 이미 존재. 백업/복원 실행 로직이 아직 없으면 최소 실행기를 주입 가능한 형태로 만들되(테스트에서 모의), 파괴적 동작은 확인 단계 뒤에서만 호출.
