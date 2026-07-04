# Final Python to PHP Cutover Plan

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 Python 참조 구현에서 PHP shared hosting 배포본으로 최종 운영 경로를
전환할 때의 최소 계획을 고정한다. 범위는 데이터, route, config, rollback
체크포인트이며, 새 기능 구현이나 배포 자동화는 다루지 않는다.

## 목적과 범위

- **대상**: 운영자, 배포 담당자, 최종 cutover 승인자.
- **전환 대상**: 일반 트래픽, 공개 route, 운영 설정, 데이터 쓰기 경로.
- **다루는 것**:
  - Python 운영 경로를 freeze하고 PHP 배포본으로 트래픽을 여는 순서.
  - DB schema version, portable backup, 쓰기 중단 기준을 포함한 데이터 확인.
  - PHP route parity와 document root 전환 확인.
  - Python/PHP config 값 대응과 secret 보존.
  - 실패 시 Python 운영 경로로 되돌리는 rollback 기준.
- **다루지 않는 것**:
  - PHP 기능 구현 또는 parity 테스트 작성.
  - DB 마이그레이션 도구 구현.
  - 호스팅사 제어판 자동화.

## 1. Cutover 시작 조건

최종 전환은 아래 조건이 모두 충족된 뒤에만 시작한다.

- [ ] `docs/php-replacement-readiness-checklist.md` 기준으로 전환 대상 모듈이
      ready 상태다.
- [ ] `docs/php-ui-readiness-gate.md`와 `docs/shared-hosting-qa-checklist.md`의
      필수 항목이 통과했다.
- [ ] PHP 배포본의 `php/VERSION`, `php/deployment-package-manifest.json`,
      `php/composer.lock` 또는 `php/vendor/`가 같은 릴리스 기준이다.
- [ ] Python 운영 경로와 PHP 운영 경로가 같은 DB schema version을 기대한다.
- [ ] rollback에 사용할 이전 Python 릴리스 파일, config, DB 백업 또는 portable
      export가 확보되어 있다.

이 조건 중 하나라도 실패하면 cutover를 시작하지 않는다. 특히 PHP가 아직 Python을
호출해야 동작하는 상태라면 최종 전환으로 보지 않는다.

## 2. 데이터 계획

데이터 전환은 "복사 후 검증"이 아니라 같은 운영 DB를 PHP가 이어받는 것을 기본값으로
한다. 단, cutover 직전에는 쓰기 경로를 멈추고 재개 가능성을 확인한다.

절차:

1. Python 앱을 maintenance mode 또는 읽기 전용 모드로 전환해 새 문서, 리비전,
   토론 댓글, 사용자 세션 변경을 중단한다.
2. 현재 DB schema version과 적용된 마이그레이션 목록을 기록한다.
3. `docs/portable-backup-format.md` 기준의 백업 또는 export를 생성한다.
4. PHP installer 또는 diagnostics에서 같은 schema version을 읽는지 확인한다.
5. 문서, 리비전, 사용자 세션, ACL, 토론, audit, jobs 테이블의 row count를 기록한다.
6. PHP에서 대표 문서 조회, 로그인 세션 확인, 문서 작성 dry run 또는 staging write를
   확인한다.

데이터 불일치가 발견되면 PHP 트래픽을 열지 않는다. 이미 일부 PHP 쓰기가 발생했다면
rollback 전에 해당 쓰기 범위와 Python 코드의 backward compatibility를 먼저 판단한다.

## 3. Route 전환 계획

route 전환은 공개 document root를 PHP `php/public/`으로 바꾸는 작업과, 기존 Python
route가 PHP route로 같은 의미를 제공하는지 확인하는 작업을 분리한다.

필수 route 확인:

- [ ] `/health`가 PHP 런타임, DB 연결 상태, schema version을 표시한다.
- [ ] `/` 또는 기본 문서 route가 PHP UI로 열린다.
- [ ] `/documents/{title}` 조회가 Python의 기존 문서 URL과 같은 canonical URL을 쓴다.
- [ ] 문서 작성/편집/검색/로그인 route가 `docs/ui-route-parity-matrix.md`의 PHP
      상태와 일치한다.
- [ ] `/installer` 또는 `/admin/diagnostics`는 공개 전환 후에도 관리자만 접근 가능하다.
- [ ] Python API route가 남아 있다면 공개 트래픽에서 사용하지 않도록 rewrite 또는
      reverse proxy 설정을 제거한다.

전환 순서:

1. PHP 배포본을 별도 릴리스 경로에 업로드한다.
2. PHP route smoke test를 임시 URL, preview domain, 또는 hosts 파일 기반으로 확인한다.
3. document root 또는 release symlink를 Python 앱에서 `php/public/`으로 전환한다.
4. 정적 asset과 HTML cache를 지운다.
5. 실제 공개 URL에서 `/health`, 문서 조회, 로그인, 문서 작성, 검색을 확인한다.

## 4. Config 전환 계획

운영 config는 Python 설정 파일을 PHP 파일로 단순 복사하지 않고, 의미가 같은 값만
명시적으로 대응한다.

확인 항목:

- [ ] DB DSN, username, password, charset, timezone이 `php/config/database.php` 또는
      호스팅 환경변수에 반영되어 있다.
- [ ] `APP_ENV`, debug flag, base URL, cookie domain, secure cookie, session lifetime이
      Python 운영값과 같은 의미다.
- [ ] secret key, CSRF/session secret, mail 설정은 새 샘플 파일로 덮어쓰지 않았다.
- [ ] writable directory(`storage/cache`, `storage/uploads`, `storage/logs`,
      `storage/exports`)가 PHP 프로세스 권한으로 읽고 쓸 수 있다.
- [ ] Python 전용 설정(`uvicorn`, ASGI worker, FastAPI middleware)은 PHP config로
      옮기지 않는다.

config 전환 후에는 `docs/config-file-permission-policy.md` 기준으로 sample config와
운영 config 권한을 다시 확인한다.

## 5. Rollback 계획

rollback의 기본값은 "Python 운영 경로 전체로 되돌리기"다. PHP 파일 일부만 되돌리거나
Python/PHP 코드를 섞어 운영하지 않는다.

rollback 시작 기준:

- [ ] PHP front controller가 fatal error를 낸다.
- [ ] schema version이 PHP 요구사항과 맞지 않아 주요 route가 실패한다.
- [ ] 문서 조회, 로그인, 문서 작성, 검색 중 하나가 공개 전환 직후 실패한다.
- [ ] PHP 쓰기 경로가 Python과 호환되지 않는 데이터 형식을 생성했다.
- [ ] config 또는 secret 누락으로 세션, CSRF, DB 연결이 실패한다.

rollback 순서:

1. maintenance mode를 켜고 PHP 쓰기 경로를 즉시 중단한다.
2. PHP 전환 이후 발생한 DB 쓰기 범위와 schema version을 기록한다.
3. `docs/shared-hosting-rollback-procedure.md` 기준으로 document root를 이전 Python
   운영 경로로 되돌린다.
4. Python config와 secret 파일이 전환 전 값인지 확인한다.
5. PHP 전환 중 적용된 DB 마이그레이션이 Python backward compatibility를 깨는지
   확인한다.
6. 필요하면 cutover 직전 백업 또는 portable export를 복원한다.
7. Python `/health`, 문서 조회, 로그인, 문서 작성, 검색을 확인한 뒤 maintenance mode를
   해제한다.

DB schema가 이미 Python과 호환되지 않는 상태라면 코드를 먼저 되돌리지 않는다.
일반 트래픽을 닫은 상태에서 데이터 보정 또는 백업 복원 여부를 먼저 결정한다.

## 6. Cutover 후 검증

전환 완료 후 첫 30분 동안 아래 항목을 확인하고 운영 기록에 남긴다.

- [ ] 공개 URL이 PHP `php/public/`에서 응답한다.
- [ ] Python 앱 프로세스, ASGI worker, Python reverse proxy route가 더 이상 공개
      트래픽을 받지 않는다.
- [ ] DB schema version과 row count가 전환 전 기록과 설명 가능한 차이만 가진다.
- [ ] PHP error log에 fatal error, class autoload 오류, DB connection 오류가 없다.
- [ ] 문서 조회, 문서 작성, 검색, 로그인, logout, diagnostics가 정상 응답한다.
- [ ] rollback 가능 시각, 백업 위치, 복원한 config 파일 목록을 기록했다.

cutover가 성공하면 Python 구현은 즉시 삭제하지 않는다. 일정 기간 읽기 전용 참조
구현과 fixture 기준선으로 보존하고, 삭제 작업은 별도 태스크에서 다룬다.

## 관련 문서

- [PHP Replacement Strategy](php-replacement-strategy.md) — Python/PHP 전환 원칙과
  금지 결합.
- [PHP Replacement Readiness Checklist](php-replacement-readiness-checklist.md) —
  모듈별 ready 판정.
- [PHP UI Readiness Gate](php-ui-readiness-gate.md) — 웹호스팅 배포 전 UI 완료 조건.
- [UI Route Parity Matrix](ui-route-parity-matrix.md) — Python/PHP route 대응 상태.
- [Shared Hosting Upgrade Procedure](shared-hosting-upgrade-procedure.md) — PHP 릴리스
  파일 전환 절차.
- [Shared Hosting Rollback Procedure](shared-hosting-rollback-procedure.md) — 코드와 DB
  호환성을 포함한 rollback 절차.
- [Portable Backup Format](portable-backup-format.md) — 백업/export 형식.
- [Config File Permission Policy](config-file-permission-policy.md) — 운영 config 권한.
