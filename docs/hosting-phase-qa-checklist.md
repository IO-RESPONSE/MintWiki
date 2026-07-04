# Hosting Phase QA Checklist

이 문서는 로드맵 **Phase E: Shared Hosting Packaging and Installer,
0611-0670** (`docs/php-db-ui-micro-job-prompts-0351-0670.md`) 의 산출물이
회귀 없이 유지되고 있는지 확인하기 위한 체크리스트다.
`docs/php-runtime-phase-qa-checklist.md`(Phase B), `docs/db-phase-qa-checklist.md`
(Phase C), `docs/php-ui-phase-qa-checklist.md`(Phase D)와 동일한 역할을
Phase E에 대해 수행한다.

`docs/shared-hosting-qa-checklist.md`가 "실제 배포본을 설치·업그레이드·
롤백할 때" 사람이 따라가는 운영 절차 체크리스트라면, 이 문서는 "Phase E가
약속한 코드/문서 산출물이 지금도 계약대로 존재하고 자동 테스트로
뒷받침되는가"를 확인하는 phase 회귀 체크리스트다. 두 문서는 서로 다른
질문에 답하며, 이 문서는 후자를 다룬다.

태스크 0669 Notes가 지정한 네 영역 — **installer, package, security,
rollback** — 을 절 단위로 다룬다. 각 항목은 "무엇을 확인하는가"와
"어떤 자동화가 이미 이를 커버하는가"를 함께 적는다. 자동화가 있다고
해서 항목을 건너뛰어도 된다는 뜻은 아니다.

## 사용법

```bash
cd php && composer install && cd -
php/scripts/qa.sh
scripts/qa.sh
```

`php` CLI가 설치되어 있으면 `scripts/qa.sh`가 `php/scripts/qa.sh`를 선택
실행하므로(0431), 위 명령 통과만으로 아래 1~4절이 참조하는 PHP 테스트
대부분이 자동으로 확인된다. `php` CLI가 없는 환경에서는 `scripts/qa.sh`가
PHP QA를 명확히 skip하므로, 이 체크리스트를 사람이 별도로 훑어봐야
한다. 문서 자체의 무결성(참조하는 파일이 실제로 존재하는지)은
`tests/test_hosting_phase_qa_checklist_doc.py`로 검증한다.

## 1. Installer

- [ ] `php/src/Installer/InstallerRouteGate.php`가 설치 완료 후 `/installer`
      경로 재접근을 차단한다. See
      `php/tests/Persistence/InstallerRouteGateTest.php`,
      `docs/installer-lock-file-policy.md`.
- [ ] `php/src/Installer/InstallerLock.php`가 lock file 생성/존재 확인을
      제공하고, 설치 완료 판정과 재실행 차단의 근거가 된다. See
      `php/tests/Persistence/InstallerLockTest.php`.
- [ ] installer requirement check가 PHP 버전, writable directories 등
      요구사항을 확인한다. See
      `php/tests/Persistence/InstallerRequirementCheckTest.php`.
- [ ] installer DB 연결 확인이 실제 schema 적용 전에 DSN/자격 증명을
      검증한다. See `php/tests/Persistence/InstallerDBCheckTest.php`.
- [ ] installer schema apply 단계가 dry-run/confirm 흐름을 유지한다. See
      `php/tests/Persistence/InstallerSchemaApplyTest.php`.
- [ ] `php/src/Ui/InstallWelcomePage.php`, `php/src/Ui/InstallRequiredPage.php`,
      `php/src/Ui/InstallDBFormPage.php`, `php/src/Ui/InstallAdminAccountFormPage.php`,
      `php/src/Ui/InstallCompletionPage.php`가 설치 마법사의 각 단계(진입 →
      요구사항 확인 → DB 설정 → 관리자 계정 → 완료)를 순서대로
      구성한다. See `php/tests/Ui/InstallWelcomePageTest.php`,
      `php/tests/Ui/InstallRequiredPageTest.php`, `php/tests/Ui/InstallDBFormPageTest.php`,
      `php/tests/Ui/InstallAdminAccountFormPageTest.php`, `php/tests/Ui/InstallCompletionPageTest.php`.
- [ ] `docs/php-ui-installer-link-policy.md`가 정한 installer 화면 간
      링크/redirect 규칙과 실제 페이지 구현이 어긋나지 않는다.

## 2. Package

- [ ] `php/deployment-package-manifest.json`이 `include`/`optional_include`
      (`with_vendor`/`without_vendor`)/`exclude` 목록을 schema version과
      함께 명시한다. See `tests/test_php_deployment_package_manifest.py`.
- [ ] `php/scripts/build-package.sh`가 실행 가능한 파일이며
      `--with-vendor`/`--without-vendor` 모드를 구분해 manifest 기준
      입력 목록을 산출한다. See `tests/test_php_package_build_script.py`.
- [ ] `docs/no-composer-hosting-deployment.md`가 composer 없이 vendor를
      사전 업로드하는 배포 절차를 설명한다.
- [ ] `docs/composer-hosting-deployment.md`가 composer 사용 가능 호스팅의
      install/update 절차를 설명한다.
- [ ] `php/scripts/README.md`가 `build-package.sh`의 역할과 현재 골격
      단계에서 실제 아카이브 생성이 후속 태스크 범위임을 명시한다.

## 3. Security

- [ ] `php/src/Security/PathTraversalGuard.php`가 config/storage 접근 시
      경로 이탈을 차단한다. See
      `php/tests/Security/PathTraversalGuardTest.php`,
      `docs/shared-hosting-security-checklist.md`.
- [ ] `php/src/Security/BackupDownloadGuard.php`가 관리자 권한과 path
      guard를 모두 요구한다. See
      `php/tests/Security/BackupDownloadGuardTest.php`.
- [ ] `php/src/Security/CsrfTokenService.php`가 상태 변경 form의 CSRF
      토큰 발급/검증 계약을 제공한다. See
      `php/tests/Security/CsrfTokenServiceTest.php`.
- [ ] `php/src/Security/PhpSessionAdapter.php`가
      `docs/shared-hosting-session-policy.md`, `docs/cookie-security-policy.md`
      가 정한 secure/httponly/samesite 기준과 일치한다. See
      `php/tests/Security/PhpSessionAdapterTest.php`.
- [ ] `php/tests/Http/HtmlSecurityHeadersTest.php`가 응답 보안 헤더
      존재를 검증한다.
- [ ] `docs/shared-hosting-security-checklist.md`의 public path/config/
      installer/permissions 절이 위 구현들과 어긋나지 않는다.

## 4. Rollback

- [ ] `docs/shared-hosting-rollback-procedure.md`가 rollback 결정 기준과
      코드/DB 복원 절차를 정의한다.
- [ ] `docs/php-ui-rollback-checklist.md`가 UI 배포분 rollback 시 확인할
      화면별 체크 항목을 제공한다. See
      `tests/test_php_ui_rollback_checklist_doc.py`.
- [ ] `docs/final-python-to-php-cutover-plan.md`가 최종 cutover 실패 시
      되돌리는 rollback 절차를 데이터/route/config 관점에서 포함한다.
      See `tests/test_final_python_to_php_cutover_plan_doc.py`.
- [ ] `php/scripts/post-cutover-validate.sh`가 cutover 직후(또는 rollback
      직후) `/health`, DB 연결/schema, 문서 생성/조회 순서로 검증 계획을
      출력한다. See `tests/test_php_post_cutover_validation_script.py`.
- [ ] `php/src/App/MaintenanceModeConfig.php`가 rollback 작업 중
      maintenance mode on/off 전환의 config 기반 골격을 제공한다.
- [ ] 위반이 있으면 `scripts/qa.sh`(PHP CLI 존재 시 `php/scripts/qa.sh`
      경유) 또는 관련 `tests/test_*.py`가 실패로 드러난다.

## 이 체크리스트가 다루지 않는 것

- 실제 배포 환경에서 설치기/롤백을 수동으로 실행하는 절차 —
  `docs/shared-hosting-qa-checklist.md`의 1절(설치 QA), 3절(Rollback QA)
  담당.
- 호스팅사별 제어판 조작 방법 —
  `docs/shared-hosting-provider-checklist-samples.md` 담당.
- 성능/부하 특성 — `docs/shared-hosting-performance-checklist.md` 담당.
- Phase E 완료 여부의 최종 판정 — 0670(0351-0670 완료 요약)이 별도로
  다룬다.

## 관련 문서

- `docs/php-runtime-phase-qa-checklist.md` — Phase B QA 체크리스트, 이
  문서가 형식을 따른 선행 문서.
- `docs/db-phase-qa-checklist.md` — Phase C QA 체크리스트.
- `docs/php-ui-phase-qa-checklist.md` — Phase D QA 체크리스트.
- `docs/shared-hosting-qa-checklist.md` — 실제 배포본 설치/업그레이드/
  롤백/forms/admin 운영 QA 체크리스트(0660).
- `docs/shared-hosting-security-checklist.md` — public path, config,
  installer, permissions 보안 점검(0658).
- `docs/shared-hosting-rollback-procedure.md` — rollback 결정 기준과
  복원 절차(0645).
- `docs/php-ui-rollback-checklist.md` — UI 배포분 rollback 체크리스트(0609).
- `docs/final-python-to-php-cutover-plan.md` — 최종 cutover 계획(0666).
- `docs/installer-lock-file-policy.md` — installer 재실행 차단 정책(0656).
- `docs/php-db-ui-micro-job-prompts-0351-0670.md` — Phase E(0611-0670)
  전체 태스크 목록.
- `php/scripts/README.md` — `build-package.sh`, `post-cutover-validate.sh`
  등 `php/scripts/` 동작 상세.
