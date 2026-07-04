# Shared Hosting Provider Checklist Samples

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 shared hosting 제공자별로 배포 전후에 복사해 사용할 수 있는 샘플
체크리스트를 제공한다. 기준 환경은 cPanel, Plesk, plain FTP 계정이며, 공통
요구사항은 `docs/shared-hosting-target-baseline.md`와
`docs/shared-hosting-qa-checklist.md`를 따른다.

## 목적과 범위

- **대상**: shared hosting 운영자, 배포 담당자, 수동 설치 QA 담당자.
- **다루는 것**:
  - cPanel 계정에서 확인할 PHP, document root, database, file manager 항목.
  - Plesk 계정에서 확인할 PHP handler, hosting settings, database, logs 항목.
  - SSH 없이 FTP만 가능한 계정에서 확인할 패키지, 업로드 순서, 권한 항목.
- **다루지 않는 것**:
  - 특정 호스팅사의 화면 자동화.
  - production 배포 대행 절차.
  - 서버 루트 권한이 필요한 Apache, Nginx, PHP-FPM 전역 설정.

## 사용법

아래 샘플 중 실제 제공자 유형에 맞는 절을 복사해 릴리스 기록에 붙이고, 각 항목을
설치 전후로 표시한다. 제공자 UI 이름은 호스팅사마다 다를 수 있으므로, 같은 의미의
메뉴를 사용해 확인한다.

공통으로 먼저 확인할 항목:

- [ ] PHP 8.1 이상과 `pdo_mysql` 확장이 제공된다.
- [ ] MariaDB 또는 MySQL 데이터베이스를 만들 수 있다.
- [ ] document root를 `php/public/`으로 지정할 수 있거나, 그에 준하는 공개 경로를
      구성할 수 있다.
- [ ] `php/src/`, `php/config/`, `php/vendor/`, `storage/`, `db/`가 웹에서 직접 열리지
      않는다.
- [ ] `storage/cache/`, `storage/uploads/`, `storage/logs/`에 PHP 런타임 쓰기 권한이
      있다.

## 1. cPanel 샘플 체크리스트

cPanel 계정은 일반적으로 MultiPHP Manager, MySQL Databases, File Manager, Metrics
또는 Errors 화면을 사용한다.

### 1.1 설치 전

- [ ] MultiPHP Manager에서 대상 도메인의 PHP 버전이 8.1 이상이다.
- [ ] Select PHP Version 또는 PHP Extensions에서 `pdo`, `pdo_mysql`, `json`, `mbstring`,
      `fileinfo` 상태를 확인했다.
- [ ] Domains 또는 Subdomains 화면에서 document root가 `php/public/` 또는 배포본의
      공개 디렉터리를 가리킨다.
- [ ] MySQL Databases에서 데이터베이스, 사용자, 사용자 권한을 만들었고 DB 호스트명을
      기록했다.
- [ ] File Manager에서 `php/config/`와 `storage/`가 `public_html` 밖에 있거나 URL로
      직접 접근할 수 없는 구조다.
- [ ] SSH와 Composer 사용 가능 여부에 따라 `without_vendor` 또는 `with_vendor`
      패키지를 선택했다.

### 1.2 업로드와 설치

- [ ] `with_vendor` 패키지를 쓰는 경우 `php/vendor/`를 먼저 올리고 `php/public/`을
      마지막에 올렸다.
- [ ] SSH와 Composer를 쓰는 경우 `php/` 디렉터리에서
      `composer install --no-dev --prefer-dist --classmap-authoritative`를 실행했다.
- [ ] File Manager 또는 SSH에서 `storage/cache/`, `storage/uploads/`, `storage/logs/`
      권한을 `750` 또는 호스팅 권장 최소 권한으로 설정했다.
- [ ] 브라우저에서 `/installer`를 열어 PHP 버전, PDO MariaDB 드라이버, URL rewrite,
      writable directories 상태를 확인했다.
- [ ] 설치 완료 후 `storage/installer/install.lock`이 document root 밖에 생성되었다.

### 1.3 배포 후

- [ ] `/installer` 재접근이 403 또는 `installation_already_complete`로 차단된다.
- [ ] `https://example.com/vendor/`, `https://example.com/config/`,
      `https://example.com/storage/` 요청이 403 또는 404를 반환한다.
- [ ] cPanel Errors 또는 error log에서 `Failed opening required vendor/autoload.php`,
      `Class not found`, DB 연결 실패가 새로 발생하지 않는다.
- [ ] 로그인, 문서 보기, 문서 편집, 검색 smoke test가 성공한다.

## 2. Plesk 샘플 체크리스트

Plesk 계정은 일반적으로 Hosting Settings, PHP Settings, Databases, File Manager,
Logs 화면을 사용한다.

### 2.1 설치 전

- [ ] Hosting Settings에서 document root가 `php/public/` 또는 배포본의 공개
      디렉터리를 가리킨다.
- [ ] PHP Settings에서 PHP 버전이 8.1 이상이며 Apache 또는 FPM handler가 계정에서
      지원된다.
- [ ] PHP Settings에서 `pdo_mysql`, `json`, `mbstring`, `fileinfo` 확장 상태를 확인했다.
- [ ] Databases 화면에서 MariaDB/MySQL 데이터베이스와 전용 사용자를 만들었고,
      접속 호스트명과 포트를 기록했다.
- [ ] File Manager에서 `php/src/`, `php/config/`, `php/vendor/`, `storage/`, `db/`가
      document root 밖에 있다.
- [ ] Composer 메뉴 또는 SSH 터미널 사용 가능 여부에 따라 배포 패키지 옵션을 정했다.

### 2.2 업로드와 설치

- [ ] Composer 메뉴를 사용하는 경우 install 명령이 `--no-dev`와
      classmap authoritative autoload 기준으로 실행되는지 확인했다.
- [ ] Composer를 사용할 수 없으면 `with_vendor` 패키지를 올리고 `php/vendor/autoload.php`
      존재를 확인했다.
- [ ] File Manager에서 `storage/cache/`, `storage/uploads/`, `storage/logs/`에 PHP handler가
      쓸 수 있는 최소 권한을 부여했다.
- [ ] `.htaccess`가 허용되는 Apache 환경이면 rewrite 규칙이 적용되는지 확인했다.
- [ ] Nginx-only 또는 proxy mode 제한이 있으면 제공자 설정에서 front controller
      라우팅 가능 여부를 먼저 확인했다.

### 2.3 배포 후

- [ ] `/installer` 또는 diagnostics 화면에서 PHP 버전, DB driver, schema version,
      writable directory 상태가 정상이다.
- [ ] Logs 화면에서 PHP fatal error, rewrite failure, 권한 오류가 새로 쌓이지 않는다.
- [ ] `composer.json`, `composer.lock`, `vendor/`, `config/`, `storage/` URL 직접 접근이
      403 또는 404로 차단된다.
- [ ] 정적 asset이 `php/public/assets/`에서 200 응답하고 HTML과 다른 cache header를
      사용한다.

## 3. Plain FTP 샘플 체크리스트

plain FTP 계정은 SSH, Composer, 심볼릭 링크 전환을 사용할 수 없다고 가정한다.
배포자는 로컬 또는 CI에서 `with_vendor` 패키지를 만든 뒤 FTP/File Manager로 올린다.

### 3.1 설치 전

- [ ] 호스팅 패널 또는 지원 문서에서 PHP 8.1 이상, `pdo_mysql`, MariaDB/MySQL 지원을
      확인했다.
- [ ] FTP 계정이 document root와 그 상위 비공개 디렉터리 모두에 접근할 수 있다.
- [ ] document root를 변경할 수 없으면 공개 디렉터리에 `php/public/` 내용만 올리고,
      `php/src/`, `php/config/`, `php/vendor/`, `storage/`, `db/`를 웹 접근 불가 위치에
      둘 수 있는지 확인했다.
- [ ] 로컬 또는 CI에서 호스팅 PHP 주 버전과 맞춰 `with_vendor` 패키지를 만들었다.
- [ ] DB 자격증명을 FTP 전송 로그나 공유 문서에 평문으로 남기지 않는 절차를 정했다.

### 3.2 업로드와 설치

- [ ] `php/vendor/`와 `php/composer.lock`을 포함한 패키지를 사용한다.
- [ ] FTP 전송 모드는 binary 또는 자동 모드를 사용하고, 전송 실패 파일 목록이 비어 있다.
- [ ] 업로드 순서는 `php/vendor/`, `php/src/`, `php/config/*.sample`, `db/schema/`,
      `storage/`, `php/public/` 순서로 진행했다.
- [ ] 덮어쓰기 배포라면 maintenance mode를 켠 뒤 `php/public/`을 마지막에 교체했다.
- [ ] FTP 클라이언트의 size 비교 또는 checksum 기능으로 `php/vendor/autoload.php`와
      주요 asset 파일 전송 완료를 확인했다.
- [ ] 쓰기 디렉터리는 FTP/File Manager에서 가능한 최소 권한으로 설정하고, 임시 `777`
      권한은 운영 전 되돌렸다.

### 3.3 배포 후

- [ ] `/installer`가 PHP fatal error 없이 열리고 requirement check가 통과한다.
- [ ] 설치 완료 후 `storage/installer/install.lock`이 생성되고 `/installer` 재실행이
      차단된다.
- [ ] `vendor/autoload.php` 누락, 대소문자 불일치, 부분 업로드로 인한 오류가 error log에
      없다.
- [ ] `php/public/assets/` 아래 CSS와 JavaScript가 200 응답한다.
- [ ] 로그인, 문서 보기, 문서 편집, 검색 smoke test가 성공한다.

## 관련 문서

- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — PHP/PDO/MariaDB
  공용 웹호스팅 요구사항.
- [Shared Hosting QA Checklist](shared-hosting-qa-checklist.md) — 설치, 업그레이드,
  rollback, forms, admin QA 기준.
- [Composer Hosting Deployment](composer-hosting-deployment.md) — Composer 실행 가능
  호스팅 배포 절차.
- [No-Composer Hosting Deployment](no-composer-hosting-deployment.md) — Composer 없는
  호스팅의 `vendor/` 사전 업로드 절차.
- [Public Docroot Policy](public-docroot-policy.md) — `php/public/` document root 기준.
- [Writable Directories Policy](writable-directories-policy.md) — 쓰기 디렉터리 위치와
  권한 기준.
