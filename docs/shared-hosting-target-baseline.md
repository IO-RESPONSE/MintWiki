# Shared Hosting Target Baseline

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.

이 문서는 이 프로젝트가 배포를 목표로 하는 공용 웹호스팅(shared hosting) 환경의
최소 기술 요구사항을 명시한다. 호스팅 제공자를 선택할 때, 애플리케이션 서버 설정을 할 때,
배포 및 운영 절차를 기획할 때 이 기준을 따른다.

`docs/portability-glossary.md`가 정의한 "Shared Hosting" 개념을 기술 요구사항으로 구체화하는
문서이다.

## 목적과 범위

- **대상**: 호스팅 제공자 선택, 서버 설정, 배포 준비 담당자.
- **다루는 것**:
  - PHP 런타임 버전 요구사항
  - 데이터베이스 연결 방식(PDO)과 지원 엔진(MariaDB)
  - URL rewrite 지원 요구사항

- **다루지 않는 것**:
  - 개별 호스팅사 설정 GUI (cPanel, Plesk 등) — 각 호스팅 매뉴얼 참고.
  - PHP 확장 추가 설치 또는 커스텀 PHP 빌드 — shared hosting은 기본 PHP만 가정.
  - 성능 튜닝, SSL/TLS 설정 등 고급 옵션 — 별도 운영 문서에서 다룬다.

## 1. PHP 런타임 버전

### 1.1 최소 요구사항

**PHP 8.1 이상**이 필수이다.

| 버전 | 상태 | 사유 |
|---|---|---|
| PHP 7.4 이하 | ❌ 불지원 | type system, match 표현식, named arguments, attributes 미지원 |
| PHP 8.0 | ❌ 불지원 | named arguments 구문 부분 지원 (match는 있지만 incomplete) |
| **PHP 8.1+** | ✓ 필수 | **readonly 속성**, **enum**, **fibers**(선택), 타입 안정성 |
| PHP 8.2, 8.3+ | ✓ 지원 | 이후 버전도 호환성 보장. 대부분의 호스팅이 8.1+ 제공. |

### 1.2 배포 확인

호스팅 계정 선택 시:

```bash
# 호스팅 제공자 관리 패널(cPanel, Plesk 등)에서:
# 1. 사용 가능한 PHP 버전 확인 (일반적으로 8.1, 8.2, 8.3 중 선택)
# 2. 기본값이 8.1+ 이상으로 설정되어 있는지 확인
# 3. 도메인별로 PHP 버전을 전환할 수 있는지 확인 (PHP 8.0 폴백 불가)

# 배포 후 버전 확인:
php -v
# PHP 8.1.x 또는 그 이상이 출력되어야 함
```

### 1.3 PHP 확장 요구사항

다음 확장은 **표준 PHP 설치에 포함**되며, 호스팅사가 별도 설치를 요구하지 않는다:

| 확장 | 용도 | 표준 상태 |
|---|---|---|
| **pdo** | 데이터베이스 추상층 | 표준(대부분 활성화) |
| **pdo_mysql** | MariaDB/MySQL 드라이버 | 표준(대부분 활성화) |
| **json** | JSON 인코딩/디코딩 | 표준(필수) |
| **xml** | XML 처리 | 표준(필수) |
| **pcre** | 정규식 | 표준(필수) |
| **fileinfo** | MIME 타입 탐지 | 표준(권장) |
| **hash** | 해싱 알고리즘 | 표준(필수) |
| **filter** | 입력 검증 | 표준(권장) |

**권장되는 선택 사항:**

```php
# php.ini 또는 호스팅 패널의 PHP 설정에서 확인:
# - disabled_functions: 불필요한 함수 비활성화 목록 (exec, passthru 등)
#   반드시 다음은 활성화: file_get_contents, file_put_contents, mkdir, rmdir
# - allow_url_fopen: on (권장) — remote config 로드 시 사용
# - max_execution_time: 30 이상 (권장) — 배포 스크립트 실행 시간
```

## 2. 데이터베이스 연결: PDO와 MariaDB

### 2.1 데이터베이스 엔진

**MariaDB 5.5 이상 또는 MySQL 5.7 이상**이 지원된다.
이 프로젝트는 ANSI SQL + MariaDB 호환성을 우선한다(`docs/portability-glossary.md`).

| DB 엔진 | 버전 | 상태 | 사유 |
|---|---|---|---|
| MariaDB | 5.5+ | ✓ 필수 | **기본 목표**, 오픈소스, 널리 지원됨 |
| MySQL | 5.7+ | ✓ 지원 | 호환, utf8mb4 지원 |
| PostgreSQL | 모든 버전 | ❌ 불지원 | ANSI SQL 이식성 원칙 위반, shared hosting에서도 드물다 |

**호스팅 제공자 선택:**

대부분의 public shared hosting (cPanel, Plesk, DirectAdmin) 제공자는
기본값으로 MySQL/MariaDB를 제공한다.

```bash
# 호스팅 패널에서:
# 1. "MySQL 데이터베이스" 또는 "Database Manager" 섹션 확인
# 2. 제공되는 데이터베이스 엔진 및 버전 확인 (보통 MariaDB 10.x)
# 3. 데이터베이스, 사용자, 권한을 자동으로 생성할 수 있는지 확인
```

### 2.2 PDO(PHP Data Objects) 드라이버

PHP에서 데이터베이스에 연결하려면 **PDO 확장과 `pdo_mysql` 드라이버**가 필수이다.

| 항목 | 요구사항 | 상태 |
|---|---|---|
| **PDO 확장** | 활성화 | ✓ 표준(거의 모든 호스팅에서 기본 활성화) |
| **pdo_mysql 드라이버** | 활성화 | ✓ 표준(거의 모든 호스팅에서 기본 활성화) |
| **Prepared Statements** | 지원 | ✓ PDO의 기본 기능 |
| **Transactions** | 지원 | ✓ MariaDB 표준 기능 |

**배포 확인:**

```php
<?php
// 호스팅에 배포 후 다음 코드로 확인:
phpinfo();
// 또는 명령줄에서:
php -m | grep pdo

// PDO와 pdo_mysql이 확인되어야 함.
// 없다면 호스팅사 지원팀에 활성화 요청.
?>
```

**연결 문자열 형식:**

```php
// 표준 MariaDB/MySQL PDO 연결:
$dsn = 'mysql:host=localhost;dbname=wiki_db;charset=utf8mb4';
$pdo = new PDO($dsn, 'wiki_user', 'password');
```

호스팅 제공자가 제공하는 호스트명, DB명, 사용자명을 사용하면 된다.

### 2.3 문자셋 요구사항

**모든 데이터베이스, 테이블, 컬럼은 `utf8mb4` 문자셋과
`utf8mb4_bin` 또는 `utf8mb4_unicode_ci` collation을 사용해야 한다.**

이는 `docs/db-web-hosting-constraints.md`에 자세히 정의되어 있다.

```sql
-- 호스팅 관리 도구에서 데이터베이스 생성 시, 문자셋을 명시:
CREATE DATABASE wiki_db CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

-- 또는 생성 후 변경:
ALTER DATABASE wiki_db CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
```

호스팅사 패널에서 "Advanced Options" 또는 "Charset" 선택지가 없다면,
초기 설치 스크립트에서 위 명령을 실행하거나 호스팅사에 문의한다.

## 3. URL Rewrite 지원

### 3.1 Rewrite 엔진 요구사항

이 프로젝트는 **단일 front controller (`index.php`)** 패턴을 사용한다.
모든 HTTP 요청을 `index.php`로 라우팅하려면 **URL rewrite 기능**이 필수이다.

| 웹 서버 | 설정 파일 | 상태 | 공용 호스팅 기본값 |
|---|---|---|---|
| **Apache** | `.htaccess` | ✓ 필수 | ✓ 대부분 지원 (mod_rewrite) |
| **Nginx** | `nginx.conf` 또는 호스팅 패널 | ✓ 지원됨 | △ 일부 제공 (VPS 권장) |
| **IIS** (Windows) | `web.config` | ✓ 지원됨 | △ 일부 제공 |

**공용 호스팅 선택 시:**

```
Apache + mod_rewrite 활성화가 기본값인 호스팅을 선택할 것을 권장한다.
대부분의 cPanel, Plesk, DirectAdmin 호스팅이 이를 제공한다.
```

### 3.2 Apache + mod_rewrite (.htaccess)

Apache 호스팅에서 front controller를 동작시키려면 아래 규칙이 필요하다.
**이는 태스크 0613에서 `php/public/.htaccess`에 구현된다.**

```apacheconf
# php/public/.htaccess (예시)
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /

  # 존재하는 파일/디렉터리는 그대로 전달
  RewriteCond %{REQUEST_FILENAME} -f
  RewriteCond %{REQUEST_FILENAME} -d
  RewriteRule ^ - [L]

  # 나머지 요청은 index.php로 라우팅
  RewriteRule ^ index.php [QSA,L]
</IfModule>
```

**호스팅 확인:**

```bash
# 호스팅 패널에서:
# 1. Apache modules 또는 "Enabled Extensions" 섹션 확인
# 2. mod_rewrite 또는 "URL Rewriting" 활성화 상태 확인
# 3. AllowOverride이 "All" 또는 "FileInfo" 이상으로 설정되어 있는지 확인
#    (AllowOverride=None이면 .htaccess 무시됨)

# 배포 후 테스트:
# curl https://example.com/documents/123
# -> 404가 아니라 애플리케이션 응답(installer 또는 앱 페이지)이 반환되어야 함
```

### 3.3 Nginx (VPS 호스팅)

Nginx를 사용하는 VPS 또는 관리형 호스팅에서는 다음과 같은
설정이 필요하다. 이는 태스크 0614에서 `docs/nginx-rewrite-guide.md`로
제공될 예정이다.

```nginx
# nginx 설정 예시 (VPS 관리자가 설정)
server {
    listen 80;
    server_name example.com;

    root /var/www/example.com/php/public;
    index index.php;

    # 실제 파일/디렉터리가 없으면 index.php로 전달
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass php:9000;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

## 4. 호스팅 선택 체크리스트

새로운 호스팅을 계약하기 전에 아래를 확인한다.

### 4.1 필수 항목 (이 중 하나라도 부족하면 배포 불가)

- [ ] **PHP 8.1 이상** — 관리 패널의 "Select PHP Version" 또는 동등 메뉴에서 확인
- [ ] **PDO + pdo_mysql 활성화** — phpinfo() 또는 `php -m | grep pdo` 실행 확인
- [ ] **MariaDB 5.5 이상 또는 MySQL 5.7 이상** — 관리 패널의 "MySQL" 또는 "Database" 섹션에서 확인
- [ ] **Apache mod_rewrite 또는 동등 rewrite 엔진** — 관리 패널 또는 호스팅사에 문의
- [ ] **AllowOverride All 또는 AllowOverride FileInfo** (Apache) — 호스팅사에 확인 또는 `.htaccess` 업로드 테스트

### 4.2 권장 항목

- [ ] **SSH 또는 명령줄 접근** — 배포 스크립트 실행, 권한 설정을 위해 권장
- [ ] **cron job 또는 Scheduler** — 백그라운드 작업 예약 (별도 문서, Phase F)
- [ ] **SSL/TLS 인증서** (Let's Encrypt 무료) — 프로덕션 필수

## 5. 배포 환경 차이

### 5.1 로컬 개발 vs. 호스팅

**로컬 개발 환경:**
```bash
docker run -it php:8.1-cli php -v
# 개발자가 PHP 버전을 선택하고 제어 가능
```

**Shared Hosting:**
```
호스팅 제공자가 관리하는 PHP만 사용 가능.
버전 업그레이드 또는 확장 추가는 호스팅사 지원팀을 통해.
```

### 5.2 로컬 테스트 검증

배포 전에 공용 호스팅 환경과 동일하게 테스트하려면:

```bash
# php:8.1 Docker 이미지로 테스트 실행
docker run --rm -v "$(pwd)/php:/app" -w /app php:8.1-cli \
  php scripts/qa.sh

# 또는 로컬 PHP 8.1에서
php scripts/qa.sh
```

이 테스트는 shared hosting에서 사용 가능한 기본 PHP만으로
애플리케이션이 동작하는지 검증한다 (`docs/php-runtime-docker-note.md`).

## 6. 호스팅사별 예시

### 6.1 cPanel + Apache (가장 일반적)

```
✓ PHP 8.1+ 선택 가능
✓ 1-click MySQL 데이터베이스 생성
✓ Apache mod_rewrite 기본 활성화
✓ .htaccess 지원
✓ SSH 접근 가능 (추가 요금)
```

### 6.2 Plesk

```
✓ PHP 8.1+ 선택 가능
✓ 데이터베이스 마법사 제공
✓ Apache/Nginx 선택 가능
✓ mod_rewrite (Apache) 또는 try_files (Nginx) 지원
```

### 6.3 DirectAdmin

```
✓ PHP 8.1+ 선택 가능
✓ MySQL/MariaDB 제공
✓ Apache mod_rewrite 기본
✓ .htaccess 지원
```

## 7. 이 문서가 하지 않는 것

- PHP 확장 추가 설치 또는 커스텀 PHP 빌드 전략 — shared hosting은
  기본 설치만 가정한다.
- 개별 호스팅 제공자 가입/설정 절차 — 각 호스팅사 튜토리얼 참고.
- 성능 튜닝 (opcache, connection pooling 등) — 별도 운영 문서에서 다룬다.
- SSL/TLS, DNS, CDN 설정 — 별도 운영 문서에서 다룬다.

## 관련 문서

- `docs/portability-glossary.md` — "Shared Hosting" 개념 정의.
- `docs/php-replacement-strategy.md` — ANSI SQL + MariaDB 이식성 원칙.
- `docs/db-web-hosting-constraints.md` — 데이터베이스 권한과 문자셋 제약.
- `docs/php-runtime-docker-note.md` — 로컬 PHP 테스트 방법.
- `docs/php-static-asset-serving.md` — 정적 asset 제공 방식.
- 태스크 0613 (`docs/php-db-ui-micro-job-prompts-0351-0670.md`) — `.htaccess` 구현.
- 태스크 0614 — nginx rewrite 문서 (예정).
- 태스크 0616 — local config loader (환경변수/파일 기반 설정).
