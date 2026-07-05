# 0702 Wire diagnostics, admin nav link, and deploy integration

## Goal

운영/파일권한 진단 화면 라우트를 등록하고, 상단바에 관리자 전용 "관리" 링크를 노출하며, 관리자 콘솔 전체(0696–0701)를 배포 패키지·런북·라이브 스모크에 통합한다.

## Phase

Phase I: Admin console wiring, 0696+.

## Scope

- php/public/index.php
- php/src/Ui/OperationalDiagnosticsPage.php, php/src/Ui/FilePermissionDiagnosticsPage.php
- php/src/Ui/NavigationBar.php (관리 링크)
- php/deployment-package-manifest.json, docs, php/scripts (smoke)
- php/tests, tests

## Acceptance Criteria

- `GET /admin/diagnostics`(OperationalDiagnosticsPage)와 `GET /admin/diagnostics/files`(FilePermissionDiagnosticsPage)를 등록하고 관리자 게이트를 적용한다.
- `NavigationBar`가 **현재 사용자가 관리자일 때만** "관리"(→ `/admin`) 링크를 상단바에 노출한다(비관리자·익명에는 숨김). 판정은 0696 게이트/ACL 재사용, 출력은 `Escaper`로 이스케이프.
- 배포 매니페스트에 관리자 화면에 필요한 공개 자산/`src/Ui/**`가 빠짐없이 포함되는지 점검·갱신한다.
- 배포 런북에 관리자 콘솔 확인 항목(로그인한 관리자만 `/admin` 접근, 비관리자 403, 익명 302, 각 하위 화면 도달)을 추가한다.
- 라이브/로컬 스모크 스크립트에 관리자 경로 점검을 보강하되, 관리자 자격 증명이 없으면 안전하게 skip한다(비인증 요청이 302/403이 되는지까지는 무자격으로 확인 가능).
- 민감정보(FTP/DB/관리자 비밀번호)는 저장소에 기록하지 않는다.
- php·py 테스트와 QA가 통과한다.

## Out of Scope

- 실제 라이브 배포 실행(자격 증명 보유 운영자가 수행).
- 진단 항목 자체의 신규 점검 추가(기존 페이지가 보여주는 범위로 한정).

## QA

- `scripts/test.sh`
- `scripts/qa.sh`

## Notes

`OperationalDiagnosticsPage`/`FilePermissionDiagnosticsPage(?Escaper, ?Layout)` 이미 존재. NavigationBar는 0690에서 로그인 상태를 이미 받는다 — 관리자 여부만 추가로 반영. 스모크 패턴은 0695 `smoke-ui-skin.sh`/`live-e2e-smoke-test.sh` 참고. 이 태스크 완료 후 운영자(자격 증명 보유)가 index.php·src/Ui·assets 변경분을 iowiki 중첩 레이아웃에 재배포한다(형제 디렉터리는 mkdir 550 트랩 때문에 `cd` 후 직접 mirror).
