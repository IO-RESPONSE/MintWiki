# Compatibility Report Template

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 공용 웹호스팅 배포본을 실제 PHP/MariaDB/hosting provider 환경에서
검증한 결과를 기록할 때 사용하는 보고서 템플릿이다. 범위는 호환성 판단에 필요한
런타임, 데이터베이스, 호스팅 제공자, 설치/업그레이드 smoke test 결과를 남기는 데
한정한다.

## 사용법

새 호스팅 환경을 검증하거나 릴리스별 호환성 확인을 수행할 때 아래 템플릿을 복사해
환경별 보고서로 작성한다. 자동 검사 결과와 수동 확인 결과를 함께 남기고, 실패한
항목은 우회 방법 또는 차단 사유를 기록한다.

보고서는 호스팅 제공자 이름만으로 환경을 단정하지 않는다. 같은 제공자라도 상품,
지역, 제어판, PHP handler, MariaDB 버전이 다를 수 있으므로 실제 확인값을 기준으로
작성한다.

## 템플릿

```markdown
# Compatibility Report: <provider>/<plan>/<date>

## 기본 정보

- **작성일**: `<YYYY-MM-DD>`
- **작성자**: `<name>`
- **대상 릴리스**: `<release-id 또는 version>`
- **호스팅 제공자**: `<provider name>`
- **호스팅 상품/플랜**: `<plan name>`
- **관리 패널**: cPanel / Plesk / DirectAdmin / 자체 패널 / 기타
- **웹 서버**: Apache / Nginx / LiteSpeed / IIS / 기타
- **결론**: 지원 / 조건부 지원 / 미지원

## PHP 결과

- **PHP 버전**: `<php -v 결과 또는 패널 표시값>`
- **PHP handler**: FPM / CGI / FastCGI / mod_php / 알 수 없음
- **필수 extension 확인**:
  - [ ] `pdo`
  - [ ] `pdo_mysql`
  - [ ] `json`
  - [ ] `mbstring`
  - [ ] `openssl`
  - [ ] `fileinfo`
- **주요 설정값**:
  - `memory_limit`: `<value>`
  - `max_execution_time`: `<value>`
  - `upload_max_filesize`: `<value>`
  - `post_max_size`: `<value>`
  - `open_basedir`: `<value 또는 없음>`
  - `disabled_functions`: `<운영에 영향 있는 항목 또는 없음>`
- **PHP 판정**: 통과 / 조건부 통과 / 실패
- **메모**: `<필요한 패널 설정, 확장 활성화 요청, 제한 사항>`

## MariaDB 결과

- **DB 엔진/버전**: `<MariaDB/MySQL version>`
- **접속 방식**: localhost socket / TCP host / remote host
- **PDO DSN 형식**: `mysql:host=<host>;dbname=<db>;charset=utf8mb4`
- **문자셋**: `<database character set>`
- **Collation**: `<database collation>`
- **권한 확인**:
  - [ ] `CREATE`
  - [ ] `ALTER`
  - [ ] `CREATE INDEX`
  - [ ] `INSERT`
  - [ ] `UPDATE`
  - [ ] `DELETE`
  - [ ] `SELECT`
  - [ ] `DROP` 또는 수동 롤백 대안
- **Schema 적용 결과**: 통과 / 조건부 통과 / 실패
- **Migration 적용 결과**: 통과 / 조건부 통과 / 실패 / 해당 없음
- **MariaDB 판정**: 통과 / 조건부 통과 / 실패
- **메모**: `<권한 부족, charset 변경 필요, 호스팅사 요청 사항>`

## Hosting Provider 결과

- **Document root 설정**: `php/public/` 가능 / 조건부 가능 / 불가
- **URL rewrite**: `.htaccess` / 패널 rewrite / Nginx 설정 요청 / 불가
- **비공개 경로 보호**:
  - [ ] `php/src/` URL 접근 차단
  - [ ] `php/config/` URL 접근 차단
  - [ ] `php/vendor/` URL 접근 차단
  - [ ] `storage/` URL 접근 차단
  - [ ] `db/` URL 접근 차단
- **Writable directory 확인**:
  - [ ] `storage/cache/`
  - [ ] `storage/uploads/`
  - [ ] `storage/logs/`
  - [ ] `storage/installer/`
- **Cron 또는 URL runner**: cron 가능 / URL trigger만 가능 / 불가
- **메일 발송**: PHP mail 가능 / SMTP 필요 / 미지원 / 미확인
- **Hosting provider 판정**: 통과 / 조건부 통과 / 실패
- **메모**: `<패널 설정, 지원팀 요청, 파일 권한 제한, rewrite 제한>`

## Smoke Test 결과

- [ ] installer requirement check가 PHP, PDO, writable directory, rewrite 상태를 표시한다.
- [ ] 새 설치 후 `storage/installer/install.lock`이 document root 밖에 생성된다.
- [ ] lock file 생성 후 `/installer` 재실행이 차단된다.
- [ ] 로그인, 문서 보기, 문서 편집, 검색이 정상 응답한다.
- [ ] `/admin/diagnostics`가 schema version과 writable directory 상태를 표시한다.
- [ ] 오류 로그에 PHP fatal error, permission denied, migration failure가 새로 쌓이지 않는다.

## 이슈와 조치

| 구분 | 심각도 | 증상 | 원인 | 조치 | 상태 |
|---|---|---|---|---|---|
| `<PHP/MariaDB/Hosting/Smoke>` | `<high/medium/low>` | `<증상>` | `<원인>` | `<조치 또는 우회>` | `<open/resolved/accepted>` |

## 최종 판정

- **전체 판정**: 지원 / 조건부 지원 / 미지원
- **조건부 지원 사유**: `<해당 없음 또는 필요한 수동 설정>`
- **미지원 사유**: `<해당 없음 또는 차단 조건>`
- **다음 확인 시점**: `<릴리스, 호스팅 설정 변경, 제공자 버전 변경 등>`

## 관련 문서

- `docs/shared-hosting-target-baseline.md`
- `docs/shared-hosting-qa-checklist.md`
- `docs/shared-hosting-security-checklist.md`
- `docs/shared-hosting-performance-checklist.md`
- `docs/mariadb-compatibility-matrix.md`
```

## 작성 기준

- PHP/MariaDB/hosting provider 결과는 각각 독립적으로 판정하고, 마지막에 전체 판정을
  남긴다.
- "조건부 지원"은 운영자가 수행해야 하는 패널 설정, 호스팅사 요청, 수동 권한 변경을
  함께 적을 때만 사용한다.
- DB 비밀번호, DSN 전체 문자열, 세션 ID, 쿠키, API key 같은 민감값은 보고서에 기록하지
  않는다.
- 실패 항목을 삭제하지 말고 이슈 표에 남긴다. 반복 검증 시 이전 실패가 해결됐는지
  추적할 수 있어야 한다.

## 관련 문서

- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — PHP, MariaDB,
  rewrite 최소 요구사항.
- [Shared Hosting QA Checklist](shared-hosting-qa-checklist.md) — 설치, 업그레이드,
  rollback, forms, admin QA 기준.
- [Shared Hosting Security Checklist](shared-hosting-security-checklist.md) — public path,
  config, installer, permissions 보안 점검.
- [Shared Hosting Performance Checklist](shared-hosting-performance-checklist.md) — opcode
  cache, static cache, DB index 점검.
- [MariaDB Compatibility Matrix](mariadb-compatibility-matrix.md) — MariaDB 타입, 인덱스,
  트랜잭션, collation 호환성 기준.
