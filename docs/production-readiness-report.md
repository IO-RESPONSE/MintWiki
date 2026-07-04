# Production Readiness Report (Placeholder)

이 문서는 Phase E(Shared Hosting Packaging and Installer, 0611-0670) 완료 후
공용 웹호스팅 production 배포 가능 여부를 판단하는 최종 검수 보고서의 골격을
고정한다.

이 태스크는 **보고서의 형식과 검수 관점만** 정의한다. 실제 production 배포,
호스팅사별 배포 대행, 자동 배포 스크립트 구현, 운영 환경 변경은 이 문서의
범위가 아니다.

## Production Readiness 정의

**Production Readiness** 는 shared hosting 대상 배포본이 다음 기준을 모두
만족하는지 최종 검수하는 것이다:

- `docs/shared-hosting-target-baseline.md` 의 PHP, PDO, MariaDB, URL rewrite 요구사항을
  충족하는가?
- `docs/public-docroot-policy.md` 와 `docs/config-file-permission-policy.md` 기준으로
  public path, 설정 파일, writable directory가 안전하게 분리되었는가?
- installer, upgrade, rollback 절차가 `docs/shared-hosting-qa-checklist.md` 에 따라
  검수되었는가?
- production 오류 응답과 로그가 `docs/production-error-handling-policy.md` 기준으로
  사용자 메시지와 내부 진단 정보를 분리하는가?
- PHP UI, DB, Python-to-PHP cutover 관련 readiness 문서가 release candidate 기준으로
  다시 확인되었는가?
- `scripts/qa.sh` 와 필요한 PHP QA가 release candidate에서 통과했는가?

## 현재 상태: Placeholder

이 문서는 production readiness를 즉시 판정하지 않는다. Phase E 마지막 검수 시점에
아래 항목을 release candidate의 실제 결과로 채워야 한다.

| 항목 | 상태 | 근거 |
|---|---|---|
| Runtime baseline | not_measured | PHP/PDO/MariaDB/rewrite 확인 전 |
| Public docroot and config isolation | not_measured | 호스팅 document root 확인 전 |
| Installer lock and reinstall guard | not_measured | 설치 완료 흐름 확인 전 |
| Writable directories | not_measured | 운영 계정 권한 확인 전 |
| Upgrade and rollback | not_measured | 백업, migration, cache clear 검수 전 |
| Production error handling | not_measured | 사용자 응답과 로그 샘플 확인 전 |
| UI and route readiness | not_measured | Phase D 이후 최종 route smoke 전 |
| Cutover readiness | not_measured | Python-to-PHP 전환 체크포인트 확인 전 |
| Automated QA | not_measured | release candidate QA 실행 전 |

상태 값은 pass, warning, fail, not_measured 중 하나로 기록한다. fail 이 하나라도
있으면 production 배포를 진행하지 않는다. warning 은 owner, 영향 범위, 후속 조치가
보고서에 명시된 경우에만 허용한다.

## 최종 검수 절차

release candidate를 production 후보로 지정한 뒤 아래 순서로 보고서를 채운다.

1. **환경 기준 확인** — PHP 버전, PDO MariaDB 드라이버, URL rewrite, document root가
   shared hosting target baseline을 만족하는지 기록한다.
2. **설치 흐름 확인** — 새 설치, installer lock file, 재설치 차단, 설정 파일 생성,
   writable directory 권한을 확인한다.
3. **운영 보안 확인** — public docroot, config 비노출, production error response,
   log redaction, session/cookie 정책을 확인한다.
4. **업그레이드와 rollback 확인** — 백업 확보, schema version, migration 적용,
   cache clear, rollback smoke test를 확인한다.
5. **애플리케이션 smoke test** — 로그인, 문서 보기, 문서 생성/수정, 검색, admin diagnostics,
   오류 페이지를 브라우저에서 확인한다.
6. **자동 검사 기록** — `scripts/qa.sh` 와 PHP QA 실행 결과, 실행 일시, release candidate
   식별자를 남긴다.
7. **최종 판정** — pass/warning/fail 항목을 요약하고 production 배포 승인 여부를 기록한다.

## 보고서 템플릿

```markdown
# Production Readiness Report

- Release candidate:
- 검수 일시:
- 검수자:
- 대상 호스팅:
- 최종 판정: pass | warning | fail

## 요약

- 전체 상태:
- 차단 이슈:
- 허용된 warning:

## 체크 결과

| 항목 | 상태 | 근거 | 후속 조치 |
|---|---|---|---|
| Runtime baseline |  |  |  |
| Public docroot and config isolation |  |  |  |
| Installer lock and reinstall guard |  |  |  |
| Writable directories |  |  |  |
| Upgrade and rollback |  |  |  |
| Production error handling |  |  |  |
| UI and route readiness |  |  |  |
| Cutover readiness |  |  |  |
| Automated QA |  |  |  |

## QA 기록

- `scripts/qa.sh`:
- PHP QA:
- 수동 smoke:

## 배포 결정

- 승인 여부:
- 승인자:
- 배포 전 필수 조치:
```

## 이 문서가 하지 않는 것

- production 배포를 자동으로 수행하지 않는다.
- `scripts/qa.sh` 에 새로운 gate를 연결하지 않는다.
- 호스팅사별 control panel 조작 절차를 새로 정의하지 않는다.
- 후속 task의 배포 자동화나 운영 기능을 선행 구현하지 않는다.

## 관련 문서

- `docs/shared-hosting-target-baseline.md` — shared hosting 최소 환경 기준.
- `docs/shared-hosting-qa-checklist.md` — 설치, 업그레이드, rollback, forms, admin QA.
- `docs/shared-hosting-security-checklist.md` — public path, config, installer 보안 점검.
- `docs/shared-hosting-upgrade-procedure.md` — 업그레이드 절차와 cache clear 기준.
- `docs/shared-hosting-rollback-procedure.md` — rollback 결정 기준과 복원 절차.
- `docs/production-error-handling-policy.md` — production 사용자 응답과 로그 분리 기준.
- `docs/php-ui-readiness-gate.md` — UI 계층 readiness gate.
- `docs/final-python-to-php-cutover-plan.md` — 최종 Python-to-PHP 전환 계획.
