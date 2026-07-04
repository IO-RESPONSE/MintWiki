# iowiki Shared Hosting Porting Log

**Phase F: Live Shared Hosting Porting, 0671+** 문서.

`iowiki.iwinv.net` FTP-only 공유 호스팅 계정에 대한 실제 포팅 실행 기록이다.
일반 정책은 `docs/shared-hosting-provider-checklist-samples.md` §3(Plain FTP)과
`docs/public-docroot-policy.md`, `docs/config-file-permission-policy.md`가
이미 정하고 있으므로, 이 문서는 그 정책을 이 계정에 적용한 결과와 이 계정 특유의
제약만 기록한다.

## 목적과 범위

- **대상**: `iowiki.iwinv.net` 계정 배포 담당자, 이후 같은 계정을 다시 다루는
  운영자.
- **다루는 것**: 이 계정에서 확인한 FTP 루트/docroot 구조, phpinfo 진단 결과,
  이 계정에 맞춘 디렉터리 배치 결정, 배포·설치·점검 절차와 사용 스크립트,
  진행 상태(완료/대기).
- **다루지 않는 것**: 일반 plain FTP 절차 자체(→
  `docs/shared-hosting-provider-checklist-samples.md`), 코드 구현.

## 1. FTP 루트 확인 결과

- FTP host: `iowiki.iwinv.net`, 계정 `iowiki`.
- FTP 로그인 직후 `pwd` = `/`.
- FTP 루트 항목: `limits/`, `public_html/` — 이 계정은 `public_html`의 형제
  디렉터리를 자유롭게 만들 수 있는 홈 디렉터리를 FTP 루트로 그대로 노출한다.
- 배포 전 `/public_html` 항목: `index.php` (호스팅사 기본 안내 페이지).

**결정**: `docs/shared-hosting-provider-checklist-samples.md` §3.1과 동일하게
`/public_html`을 배포 대상 docroot로 사용한다.

## 2. phpinfo 진단 결과 요약

`php/scripts/phpinfo-probe.sh`로 올린 임시 진단 파일 확인 결과(진단 후 삭제 완료):

| 항목 | 값 |
|---|---|
| Public docroot | `/home1/iowiki/public_html` |
| `SCRIPT_FILENAME` 샘플 | `/home1/iowiki/public_html/iowiki_phpinfo_20260703_1303_a7f4.php` |
| PHP 버전 | `8.4.16` |
| Server API | `FPM/FastCGI` |
| OS | `Linux multiphp-102.iwinv.kr 4.18.0-553.89.1.el8_10.x86_64`, RHEL 8.10 base |
| Loaded php.ini | `/etc/opt/remi/php84/php.ini` (+ `/etc/opt/remi/php84/php.d`) |
| 확인된 확장 | `curl`, `fileinfo`, `mbstring`, `mysqli`, `pdo_mysql`, `json`, `openssl`, `session` |
| `mysqli.default_host` / `default_port` / `default_socket` | `localhost` / `3306` / `/tmp/mysql.sock` |
| `pdo_mysql.default_socket` | `/tmp/mysql.sock` |
| `session.cookie_httponly` / `use_strict_mode` / `cookie_secure` | `On` / `On` / `Off` |

**docs/shared-hosting-target-baseline.md, docs/mariadb-compatibility-matrix.md
기준 대비**: PHP 8.4와 `pdo_mysql`/`mysqli` 확장은 요구사항을 충족한다.
`session.cookie_secure`가 기본 `Off`이므로, HTTPS로만 서비스한다면
`docs/shared-hosting-session-policy.md`가 정한 대로 애플리케이션 쿠키 설정에서
secure 플래그를 명시적으로 켠다(php.ini 전역 값에 의존하지 않는다).

이 계정은 `home1/iowiki`가 FTP 루트와 동일하다 — 즉 `/home1/iowiki/public_html`이
곧 `/public_html`이다. `docs/public-docroot-policy.md`가 기본으로 가정하는
`public_html/public/` 2단 구조(별도 `public/` 서브디렉터리를 docroot로 지정)는
이 계정에서 지원되지 않는다(호스팅 패널이 docroot를 `public_html` 고정으로
제공). 아래 §3은 이 차이를 반영한 배치다.

## 3. 디렉터리 배치 결정 (이 계정 전용)

| 저장소 경로 | 이 계정에서의 위치 | 웹 접근 |
|---|---|---|
| `php/public/**` (index.php, assets/) | `/public_html/` 바로 아래 | 공개(docroot) |
| `php/src/**` | FTP 루트의 `src/` (형제 디렉터리) | 접근 불가 |
| `php/vendor/**` | FTP 루트의 `vendor/` | 접근 불가 |
| `php/config/*.sample` 기반 실제 설정(`database.php` 등) | FTP 루트의 `config/` | 접근 불가 |
| `db/schema/**` | FTP 루트의 `db/` | 접근 불가 |
| `storage/{cache,uploads,logs,installer}` | FTP 루트의 `storage/` | 접근 불가 |

FTP 루트에 `config/`, `src/`, `vendor/`, `db/`, `storage/`를 새로 만드는 것은
`limits/`, `public_html/`과 같은 층에 디렉터리를 추가하는 일반 FTP `MKD` 동작이며,
사전 확인된 계정 권한(홈 디렉터리 소유자 쓰기 권한) 범위 안에 있다. 이 방식으로
`docs/public-docroot-policy.md` §2가 요구하는 "공개 디렉터리 하나만 노출" 원칙을
`public_html/public/` 서브디렉터리 없이도 만족시킨다.

MariaDB 연결 설정(`config/database.php`)은 이 `config/` 디렉터리에 두고
`docs/config-file-permission-policy.md` 기준(`chmod 640` 또는 계정 단일 사용자
환경이면 `chmod 600`)을 적용한다. 실제 DB 자격증명은 저장소에 커밋하지 않고
호스팅 계정에만 존재한다.

## 4. 배포 절차와 사용 스크립트

1. **index.php 백업** — `php/scripts/ftp-deploy.sh`가 docroot를 미러링하기
   전에 기존 `/public_html/index.php`를 `--backup-dir`(기본
   `./ftp-deploy-backups`)로 타임스탬프 파일명으로 먼저 내려받는다.
2. **배포 패키지 준비** — `php/scripts/build-package.sh --with-vendor`로
   `php/deployment-package-manifest.json`의 `with_vendor` 입력 목록을
   확인한다(이 계정은 SSH/Composer 실행이 없는 plain FTP 계정이므로
   `--with-vendor`를 선택한다. 실제 아카이브 조립은 별도 로컬/CI 빌드에서
   `include`/`optional_include.with_vendor` 목록을 그대로 복사한다).
3. **업로드** —

   ```bash
   FTP_HOST=iowiki.iwinv.net FTP_USER=iowiki \
   php/scripts/ftp-deploy.sh \
     --local-public-dir php/public \
     --private-map php/src:src \
     --private-map php/vendor:vendor \
     --private-map <local-config-dir>:config \
     --private-map db/schema:db \
     --private-map <local-storage-dir>:storage
   ```

   `FTP_PASSWORD`는 환경변수 또는 `--password-file`로만 전달한다.
4. **설치/schema 적용** — 업로드 후 `/installer`를 열어
   `docs/installer-lock-file-policy.md`가 정한 흐름(요구사항 검사 → DB 설정 →
   schema 적용 → 관리자 계정 생성 → `storage/installer/install.lock` 생성)을
   따른다. installer는 `config/database.php`에서 위 §3의 MariaDB 접속 정보를
   읽는다.
5. **스모크 테스트** — `php/scripts/live-http-smoke-test.sh --base-url
   https://iowiki.iwinv.net`로 루트 응답과 민감 경로 차단을 확인한다.

## 5. 실행 상태

| 항목 | 상태 |
|---|---|
| FTP 루트/docroot 구조 확인 (§1) | 완료 (Notes 기록 반영) |
| phpinfo 진단, 확인 후 삭제 (§2) | 완료 (Notes 기록 반영) |
| 배포 전 베이스라인 HTTP 스모크 테스트 | 완료 — 아래 결과 참고 |
| 배포 패키지 업로드 (§4-3) | **대기** — 실제 FTP 자격증명 필요 |
| 설치/schema 적용 (§4-4) | **대기** — 실제 FTP/DB 자격증명 필요 |
| 배포 후 HTTP 스모크 테스트 | **대기** — 업로드/설치 완료 후 재실행 |
| installer lock/권한/민감 파일 노출 점검 (§6) | **대기** — 설치 완료 후 수행 |

이 태스크를 실행한 세션에는 실제 FTP 계정 비밀번호와 MariaDB 비밀번호가
제공되지 않았다(0671 Notes: "실행 시점에 임시 credential 파일 또는
환경변수로만 제공한다"). 위 스크립트 3종(`ftp-deploy.sh`,
`phpinfo-probe.sh`, `live-http-smoke-test.sh`)은 실제 자격증명이 주어지는
배포 창에서 그대로 실행할 수 있도록 준비되어 있으며, `--dry-run`으로 미리
계획을 검증할 수 있다. 업로드·설치·설치 후 점검은 자격증명을 가진 운영자가
§4-§6의 절차대로 이어서 수행한다.

### 배포 전 베이스라인 스모크 테스트 결과

`php/scripts/live-http-smoke-test.sh --base-url https://iowiki.iwinv.net` 실행
결과(배포 전, 호스팅사 기본 안내 페이지 상태):

- `GET https://iowiki.iwinv.net/` → `200` (호스팅사 기본 "셋팅 완료" 페이지).
- `config/`, `config/database.php`, `vendor/`, `vendor/autoload.php`,
  `storage/`, `storage/installer/install.lock`, `db/`, `composer.json`,
  `composer.lock`, `.env` → 모두 `404`(아직 배포 전이므로 해당 경로 자체가
  없다).
- `db/schema/schema.sql`만 `302`(iwinv WAF의 `.sql` 확장자 차단 규칙이
  `https://notice.web.iwinv.kr/modsecurity/waf.html`로 리다이렉트한다). 이는
  일반 404보다 더 엄격한 차단이며 노출로 보지 않는다. 배포 후 재실행 시에도
  같은 경로가 200으로 바뀌지 않는지 반드시 다시 확인한다.

## 6. 설치 후 점검 (실행 예정 절차)

`docs/shared-hosting-security-checklist.md`와
`docs/installer-lock-file-policy.md` 기준으로, 설치 완료 후 아래 항목을
`php/scripts/live-http-smoke-test.sh`와 FTP 파일 관리자로 확인한다.

- [ ] `storage/installer/install.lock`이 FTP 루트의 `storage/installer/`
      (docroot 밖)에 생성되었다.
- [ ] `/installer` 재접근이 403 + `installation_already_complete`로 차단된다.
- [ ] `config/`, `src/`, `vendor/`, `storage/`, `db/` 아래 경로가
      `live-http-smoke-test.sh` 기준으로 403/404를 반환한다.
- [ ] `config/database.php` 권한이 `chmod 640`(또는 `600`)이다.
- [ ] `storage/cache/`, `storage/uploads/`, `storage/logs/` 권한이
      `chmod 750`이고 임시로 `777`을 쓴 경우 되돌렸다.
- [ ] 로그인, 문서 보기, 문서 작성, 검색 smoke test가 성공한다.

## 관련 문서

- [Shared Hosting Provider Checklist Samples](shared-hosting-provider-checklist-samples.md) — Plain FTP 일반 절차.
- [Public Docroot Policy](public-docroot-policy.md) — 공개/비공개 디렉터리 분리 원칙.
- [Config File Permission Policy](config-file-permission-policy.md) — 설정 파일 위치/권한.
- [Installer Lock File Policy](installer-lock-file-policy.md) — 설치 완료 차단 기준.
- [Shared Hosting Security Checklist](shared-hosting-security-checklist.md) — 배포 전후 보안 점검표.
- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — PHP/MariaDB 최소 요구사항.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — 지원 버전 기준.
- [PHP DB Configuration](php-db-config.md) — DB 연결 설정 로드 방식.
- [Writable Directories Policy](writable-directories-policy.md) — 쓰기 디렉터리 권한.
- [Shared Hosting Rollback Procedure](shared-hosting-rollback-procedure.md) — 배포 실패 시 되돌리기.
- [Final Python to PHP Cutover Plan](final-python-to-php-cutover-plan.md) — 전체 cutover 계획과의 관계.
