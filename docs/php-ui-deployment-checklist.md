# PHP UI Deployment Checklist

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 배포용 문서.
[PHP UI Architecture](php-ui-architecture.md), [PHP Static Asset Serving](php-static-asset-serving.md),
[PHP UI Cache Header Policy](php-ui-cache-header-policy.md), [PHP UI Static Asset Integrity Policy](php-ui-static-asset-integrity.md)
에서 정의한 UI 구조를 **shared hosting 환경에서 실제로 배포할 때** 확인해야 할 체크리스트다.

이 문서는 운영자 또는 배포 담당자가 UI 파일/설정을 shared hosting 환경(Apache, Nginx 등)에
업로드하기 직전과 직후에 사용한다.

`docs/php-runtime-phase-qa-checklist.md` (Phase B), `docs/db-phase-qa-checklist.md` (Phase C)
와 동일한 형식을 따른다 — 각 항목은 "무엇을 확인하는가"와 "어떤 자동화가
이미 이를 커버하는가"를 함께 적는다.

## 사용법

```bash
# 1. 로컬 테스트 (배포 전)
scripts/test.sh
scripts/qa.sh

# 2. 파일 구조와 권한 확인 (로컬)
find php/public -type f -ls | head -20
ls -la php/
ls -la php/public/assets/

# 3. shared hosting 업로드 후 (deploy 이후)
# 브라우저에서 https://example.com 방문 후 아래 절 항목들을 확인
# 개발자 도구(DevTools)의 Network/Console tab에서:
# - 정적 asset 로드 성공 여부
# - Cache-Control 헤더 값
# - 콘텐츠 타입(Content-Type) 정확성
# 등을 검증
```

## 1. 배포 파일 구조 (File Structure)

UI 파일이 shared hosting의 올바른 위치에 있고, 불필요한 파일이 배포되지 않았는지 확인한다.
해당 태스크: 0521(PHP UI template skeleton), 0522 이후 page/handler 태스크들.

### 1.1 문서 루트(DocumentRoot) 구조

- [ ] `php/public/` 디렉터리가 웹 서버의 문서 루트로 설정되었다.
      shared hosting 제어판에서 "Document Root" 또는 "Public HTML" 설정이
      이 경로를 가리킨다. See `docs/php-static-asset-serving.md`.

- [ ] `php/public/index.php` (front controller)가 정확한 위치에 있다.
      이 파일이 웹 서버의 기본 인덱스로 실행된다.

- [ ] `php/public/assets/` 디렉터리가 존재하고, CSS/JS 파일들이 그 아래에 있다.
      ```
      php/public/assets/
      ├── css/
      │   ├── design-tokens.css
      │   ├── buttons.css
      │   ├── print.css
      │   └── ...
      └── js/
          └── app.js
      ```

### 1.2 비공개 파일 위치

- [ ] `php/src/`, `php/tests/`, `db/` 디렉터리들은 **문서 루트 밖**에
      위치하며, 웹에서 직접 접근할 수 없다. 웹 브라우저에서
      `https://example.com/src/` 같은 경로로 접근 시 404가 나와야 한다.

- [ ] `.env`, `composer.lock`, `vendor/` 같은 설정/의존성 파일도
      문서 루트 밖에 있다. 악의적 사용자가 환경 변수나 라이브러리를
      직접 읽을 수 없어야 한다.

- [ ] `docs/` 디렉터리는 배포 패키지에 포함되지 않는다 (또는 포함되면
      웹 접근 불가 권한). 설계 문서가 인터넷에 공개되지 않아야 한다.

**자동화**: 배포 스크립트 또는 CI/CD 파이프라인이 `php/public/` 만 업로드하거나,
`.gitignore` 기반 배포 도구가 설정/소스 파일을 자동으로 제외해야 한다.
수동 배포 시 사람이 위 파일들을 업로드하지 않았는지 확인.

### 1.3 asset 파일 무결성

- [ ] `php/public/assets/css/` 의 모든 CSS 파일이 업로드되었다.
      로컬의 git 상태(`git ls-tree -r HEAD php/public/assets/css`)와
      shared hosting 서버의 파일 목록을 비교.

- [ ] `php/public/assets/js/` 의 모든 JavaScript 파일이 업로드되었다.
      마찬가지로 빠진 파일이 없는지 확인.

- [ ] asset 파일의 size가 로컬 버전과 일치한다. 업로드 중 손상되거나
      부분 업로드되지 않았는지 확인하기 위해 바이트 단위로 비교.
      ```bash
      # 로컬 (배포 기준)
      ls -lh php/public/assets/css/design-tokens.css
      
      # shared hosting에서 SSH/FTP로 확인
      ls -lh /path/to/public/assets/css/design-tokens.css
      ```

**자동화**: 배포 스크립트가 파일 목록과 체크섬(checksum)을 검증하면, 업로드 손상을
자동 감지할 수 있다. 그 외는 수동 확인 또는 FTP 미러링 도구의 크기 비교 기능.

## 2. 파일 권한 (File Permissions)

웹 서버가 파일을 읽을 수 있고, 불필요한 쓰기 권한이 없도록 설정한다.
해당 태스크: shared hosting 환경 설정 (Phase E 초반), 0521 이후 각 page 태스크.

### 2.1 읽기 권한 설정

- [ ] `php/public/` 의 모든 파일이 웹 서버가 읽을 수 있다(644 또는 644+실행).
      shared hosting 제어판의 File Manager 또는 SSH에서 권한 확인:
      ```bash
      ls -la php/public/index.php
      # 결과 예: -rw-r--r-- 1 user group 5234 Jul  3 10:00 index.php
      ```
      웹 서버 실행 사용자(`www-data`, `apache`, `nobody` 등)가 읽을 수 있어야 한다.

- [ ] `php/public/assets/css/`, `php/public/assets/js/` 의 모든 asset 파일이
      읽을 수 있다(644). 스타일과 스크립트가 제공되지 않으면 UI가 깨진다.

- [ ] `php/` 소스 파일(`php/src/`, `php/tests/` 등)은 644 권한으로,
      웹에서 직접 접근할 수 없지만 웹 서버가 PHP 인터프리터로 실행할 때는
      읽을 수 있어야 한다.

### 2.2 쓰기 권한 제한

- [ ] `php/public/` 의 파일들이 **쓰기 권한(write)**을 갖지 않는다(644, not 666).
      웹 서버가 배포 후 파일을 변경하면 보안 위협이다. 권한 확인:
      ```bash
      find php/public -type f | xargs ls -l | grep -E '66[0-7]|777'
      # 결과가 없어야 한다 (쓰기 권한이 있는 파일이 없어야 함)
      ```

- [ ] `php/src/`, `php/tests/` 등 비공개 파일도 쓰기 권한이 없다(644).
      악의적 사용자가 취약점을 이용해 이들 파일을 변경할 수 없어야 한다.

- [ ] 임시 파일/캐시/로그 디렉터리(`php/var/cache/`, `php/var/logs/` 등이
      있다면)만 쓰기 권한을 가진다(755 디렉터리, 644 파일). 기타 디렉터리는
      읽기만 가능(755).

### 2.3 디렉터리 권한

- [ ] `php/public/`, `php/public/assets/`, `php/public/assets/css/`,
      `php/public/assets/js/` 등 모든 디렉터리가 읽기/실행 권한을 가진다(755).
      웹 서버가 디렉터리를 탐색하고 그 아래 파일을 읽을 수 있어야 한다.
      ```bash
      find php/public -type d | xargs ls -ld
      # 결과 예: drwxr-xr-x 3 user group 4096 Jul  3 10:00 php/public/assets/
      ```

- [ ] 비공개 디렉터리(`php/src/`, `php/tests/` 등)도 755 또는 750,
      웹 서버가 탐색할 수 있되 다른 사용자는 접근할 수 없다(필요시 750).

**자동화**: 배포 스크립트가 파일/디렉터리 권한을 자동으로 설정하면 일관성을 보장한다.
그 외는 shared hosting 제어판 File Manager의 "Change Permissions" 기능 또는
SSH chmod 명령으로 수동 설정.

## 3. 정적 Asset 배포 (Static Asset Deployment)

정적 asset이 공개 경로에 올바르게 배치되고, 캐시 정책이 적용되었으며,
버전/무결성 식별자가 올바르게 작동하는지 확인한다.
해당 태스크: 0606(asset integrity policy), 0607(asset version helper), 0524(asset serving).

### 3.1 asset URL 생성

- [ ] HTML 템플릿이 asset URL을 하드코딩하지 않고, 헬퍼 함수를 통해
      생성한다. 예:
      ```php
      // ❌ 하드코딩 (업데이트 시 캐시 무효화 불가)
      <link rel="stylesheet" href="/assets/css/design-tokens.css">
      
      // ✅ 헬퍼 사용 (자동으로 버전 쿼리 추가)
      <link rel="stylesheet" href="<?= $assetVersioning->url('/assets/css/design-tokens.css') ?>">
      // 결과: /assets/css/design-tokens.css?v=abc123de
      ```
      See `docs/php-ui-static-asset-integrity.md`, task 0607.

- [ ] 모든 `<link rel="stylesheet">`, `<script src="...">` 태그가
      asset versioning helper를 사용한다. 빠진 항목이 없는지 템플릿 코드를 검토.

- [ ] asset URL이 절대 경로(`/assets/...`)로 쓰여 있다. 상대 경로(`../assets/...`)
      는 페이지별로 달라져 오류가 발생하기 쉽다.

### 3.2 asset 파일 존재 및 콘텐츠 확인

- [ ] 브라우저 DevTools의 Network tab에서 CSS/JS 파일이 모두 200 OK로 로드된다.
      ```
      /assets/css/design-tokens.css?v=abc123de        [200] 5.2 KB
      /assets/css/buttons.css?v=def456gh              [200] 3.1 KB
      /assets/js/app.js?v=hij789kl                    [200] 2.8 KB
      ```
      404 오류가 없는지 확인.

- [ ] CSS 파일이 로드되면 페이지의 스타일이 적용된다. 폰트, 색상, 레이아웃이
      예상한 대로 렌더링되는지 육안 확인.

- [ ] JavaScript 파일이 로드되면 console tab에서 script error가 없다.
      "Uncaught SyntaxError", "Uncaught ReferenceError" 등이 없어야 한다.

### 3.3 asset 캐시 무효화 (Cache Busting)

- [ ] asset URL의 버전 쿼리 매개변수(`?v=hash`)가 파일마다 다르다.
      DevTools에서 URL을 확인:
      ```
      /assets/css/design-tokens.css?v=a1b2c3d4
      /assets/css/buttons.css?v=b2c3d4e5
      /assets/js/app.js?v=c3d4e5f6
      # 각각 다른 hash 값
      ```

- [ ] 파일을 변경하면 hash가 바뀐다. 예를 들어 `design-tokens.css`에 한 줄
      추가 후 재배포하면:
      ```
      before: /assets/css/design-tokens.css?v=a1b2c3d4
      after:  /assets/css/design-tokens.css?v=x9y8z7w6  # 다른 hash
      ```
      hash가 변경되어야만 브라우저가 새 파일을 다운로드한다.

- [ ] 버전 헬퍼가 파일 변경을 감지하는 메커니즘이 동작한다.
      - 런타임 hash 계산 방식이면: PHP가 매 request마다 파일을 읽고 hash를 계산.
      - 빌드 시 manifest 방식이면: 배포 시 manifest 파일이 현재 파일 hash를 반영.
      
      로컬에서 asset 파일을 변경하고 `php -S` 로컬 서버를 띄워 hash 변경을 테스트.

**자동화**: 배포 스크립트가 asset versioning을 자동 계산하면 수동 오류를 줄인다.
task 0607에서 asset version helper 구현 후 자동화 가능. 그 전은 수동 확인 또는
헬퍼 함수의 존재만 검증.

## 4. 캐시 정책 (Cache Control Headers)

HTTP 응답 헤더의 캐시 정책이 HTML과 asset을 올바르게 구분하고,
웹 서버/CDN/브라우저 캐시가 의도한 대로 동작하는지 확인한다.
해당 태스크: 0577(cache header policy), 0578(asset cache headers).

### 4.1 HTML 응답 캐시 정책

- [ ] 모든 HTML 페이지(`/`, `/docs/`, `/search` 등)의 응답 헤더에
      `Cache-Control: no-cache, no-store, must-revalidate` 가 있다.
      DevTools Network tab에서 응답 헤더를 확인:
      ```
      GET https://example.com/docs/wiki-page
      Response Headers:
      Cache-Control: no-cache, no-store, must-revalidate
      ```
      이 정책은 `Response::html()` 메서드가 자동으로 추가한다(0577).

- [ ] 사용자가 브라우저의 새로고침(Ctrl+F5)을 할 때, 최신 HTML을 받는다.
      `no-cache` 정책 덕분에 브라우저가 항상 서버에 조건부 요청을 보낸다.

- [ ] 프록시/CDN을 거쳐도 HTML이 캐시되지 않는다. 프록시 설정이
      `Cache-Control: no-cache` 를 존중하는지 확인 (대부분의 표준 프록시는 존중).

### 4.2 정적 asset 캐시 정책

- [ ] CSS/JS 파일의 응답 헤더에 장시간 캐시 정책이 있다.
      DevTools에서 asset 파일의 응답 헤더 확인:
      ```
      GET https://example.com/assets/css/design-tokens.css?v=abc123de
      Response Headers:
      Cache-Control: public, max-age=31536000, immutable
      ```
      또는 웹 서버 설정이 이를 자동으로 추가한 경우.

- [ ] asset의 max-age가 길다(1년 = 31536000초 권장). 브라우저가 한 번 다운로드한
      파일을 재방문 시 캐시에서 읽는다.

- [ ] `immutable` 헤더가 있으면, 브라우저가 재검증(revalidation) 요청을 보내지 않는다.
      버전 쿼리 덕분에 파일이 변경되면 다른 URL로 요청되므로, 기존 캐시는 그대로
      두고 새 버전을 다운로드한다.

### 4.3 보안 헤더와의 조합

- [ ] HTML 응답이 XSS/clickjacking 방어 헤더도 포함한다:
      ```
      X-Content-Type-Options: nosniff
      X-Frame-Options: DENY
      Content-Security-Policy: default-src 'self'
      ```
      task 0554에서 정의한 기준 따름. 이들도 `Response::html()` 에 포함되어야 한다.

- [ ] 쿠키가 있으면 `Secure`, `HttpOnly` 속성이 설정되었다.
      로그인 토큰이 JavaScript에 노출되지 않고, HTTPS에서만 전송된다.

**자동화**: 배포 직후 웹 서버 설정(Apache `.htaccess`, Nginx config 등)이
HTTP 헤더를 자동으로 설정하면, 일관성을 보장한다. task 0577/0578 구현 후
자동 검증 가능. 그 전은 DevTools로 수동 확인.

## 5. 공개 경로 설정 (Public Path Configuration)

shared hosting 환경의 document root 설정이 올바르고, asset URL과 일치하는지 확인한다.
해당 태스크: 0521(template skeleton), 0524(asset serving), 0525+ 각 page 태스크.

### 5.1 document root 설정

- [ ] shared hosting 제어판에서 웹 도메인의 "Document Root" 또는
      "Public HTML" 경로가 `php/public/` 을 가리킨다.
      예:
      ```
      Domain: example.com
      Document Root: /home/user/public_html/php/public
      (또는 /var/www/example.com/php/public)
      ```

- [ ] 그 결과, 브라우저에서 `https://example.com/` 방문 시
      `php/public/index.php` 가 실행된다.

- [ ] 반대로 `https://example.com/src/` 같은 경로는 404를 반환한다.
      PHP 소스가 웹에 노출되지 않는다.

### 5.2 asset 경로 일관성

- [ ] asset URL이 `/assets/...` 절대 경로로 일관되게 쓰여 있다.
      document root가 `php/public/` 이므로:
      ```
      브라우저 요청: https://example.com/assets/css/design-tokens.css
      서버 파일: /home/user/public_html/php/public/assets/css/design-tokens.css
      웹 서버: 그대로 파일을 제공
      ```

- [ ] asset URL에 base path나 subdirectory prefix가 없다(또는 배포 구성에서
      명시적으로 추가된다). shared hosting의 document root가 이미 `php/public/` 로
      설정되어 있으면, `/assets/...` 로 충분하다.

### 5.3 front controller 라우팅

- [ ] PHP 웹 서버 설정에서 "없는 파일은 `index.php` 로 rewrite" 규칙이 있다.
      shared hosting 제어판이 자동으로 설정하는 경우가 많지만, 확인:
      ```
      # Apache (usually in .htaccess)
      <IfModule mod_rewrite.c>
          RewriteEngine On
          RewriteCond %{REQUEST_FILENAME} !-f
          RewriteCond %{REQUEST_FILENAME} !-d
          RewriteRule ^(.*)$ /index.php/$1 [L]
      </IfModule>
      
      # Nginx (in server block)
      try_files $uri $uri/ /index.php$is_args$args;
      ```

- [ ] 그 결과, `/docs/my-page` 요청은 실제 파일이 없으면 `index.php` 로 전달되고,
      front controller가 라우팅을 처리한다. 정적 asset(`/assets/...`)은 실제 파일이
      있으므로 rewrite를 거치지 않는다.

### 5.4 HTTPS와 mixed content

- [ ] 배포 도메인이 HTTPS를 지원한다. shared hosting 제어판에서 SSL 인증서가
      활성화되었는지 확인.

- [ ] asset URL이 프로토콜을 명시하지 않는다 (`/assets/...`, not `http://...`).
      프로토콜 상대 URL(protocol-relative URL) 사용 금지. 브라우저가 현재 프로토콜을
      따르므로, `/assets/...` 로 충분하다.

- [ ] 모든 리다이렉트가 HTTPS로 이루어진다. HTTP 요청은 HTTPS로 리다이렉트된다.
      웹 서버 설정:
      ```
      RewriteCond %{HTTPS} off
      RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
      ```

**자동화**: 배포 스크립트가 document root와 asset URL을 검증하면 오류를 방지한다.
그 외는 웹 서버 설정 파일 리뷰 또는 실제 요청(curl, 브라우저)으로 확인.

## 6. 배포 전 최종 검증 (Pre-Deployment Verification)

파일을 업로드하기 직전에 로컬 환경에서 수행할 자동 및 수동 검사.
해당 태스크: 전 Phase D 범위.

### 6.1 로컬 QA 실행

- [ ] 모든 테스트가 통과한다:
      ```bash
      scripts/test.sh         # 전체 Python/PHP 테스트
      scripts/qa.sh           # PHP QA (escaping, security headers 등)
      ```

- [ ] 빌드 경고나 deprecation이 없다. 배포 후 문제가 발생할 수 있는 신호.

- [ ] 로컬 PHP 서버에서 주요 페이지가 정상 렌더링된다:
      ```bash
      php -S 127.0.0.1:8000 -t php/public &
      # 브라우저: http://127.0.0.1:8000/
      ```
      첫 페이지, 문서 보기, 로그인, 폼 제출 등.

### 6.2 파일 구조 검증

- [ ] `php/public/assets/` 아래의 모든 CSS/JS 파일이 있다:
      ```bash
      find php/public/assets -type f | sort
      ```

- [ ] 배포 패키지에 불필요한 파일이 없다(`.git`, `tests/`, `docs/` 등):
      ```bash
      find php -name '.git' -o -name 'tests' -o -name 'docs'
      # 결과가 없거나, 배포에서 제외되어야 함
      ```

- [ ] 파일 권한이 올바르다 (644 파일, 755 디렉터리):
      ```bash
      find php/public -type f -perm /077 # 644가 아닌 파일 찾기
      find php/public -type d -perm /077 # 755가 아닌 디렉터리 찾기
      # 결과가 없어야 함
      ```

### 6.3 asset 무결성 검사

- [ ] asset versioning 헬퍼가 구현되었다(task 0607 완료):
      ```bash
      grep -r "assetVersioning\|assetUrl" php/src/Ui/*.php
      # 결과가 있어야 함
      ```

- [ ] HTML 템플릿이 asset versioning을 사용한다:
      ```bash
      grep -r "<link rel=" php/src/Ui/ | grep -v assetVersioning
      # 결과가 없어야 함 (모든 asset URL이 helper를 통해 생성)
      ```

**자동화**: CI 파이프라인이 이 검사들을 자동으로 수행하면, 배포 전 모든
문제를 감지할 수 있다. GitHub Actions, GitLab CI 등에서:
```yaml
test:
  script:
    - scripts/test.sh
    - scripts/qa.sh
    - # 파일 구조 검증 스크립트
deploy:
  only: [ main ]
  when: on_success
```

## 7. 배포 후 환경 검증 (Post-Deployment Verification)

파일을 shared hosting에 업로드한 직후, 실제로 서비스되는지 확인.
운영자 또는 배포 담당자가 수행.

### 7.1 첫 페이지 렌더링

- [ ] 브라우저에서 `https://example.com/` 방문:
      - 페이지가 로드된다 (timeout/500 error 없음)
      - HTML, CSS, JavaScript가 모두 로드된다 (DevTools Network tab 확인)
      - 페이지가 스타일과 함께 렌더링된다 (blank/unstyled 페이지 아님)

- [ ] 주요 UI 요소들이 보인다:
      - header/navigation
      - main content area
      - footer

### 7.2 정적 asset 로드 확인

- [ ] DevTools Network tab에서 모든 asset이 200 OK로 로드된다:
      ```
      /assets/css/design-tokens.css?v=abc123de  [200]
      /assets/js/app.js?v=def456gh              [200]
      ```

- [ ] asset 파일이 404/403 오류를 반환하지 않는다. 404면 파일이 없거나
      경로가 잘못된 것, 403이면 권한 문제.

- [ ] 콘솔(Console tab)에 JavaScript 오류가 없다:
      - "Uncaught SyntaxError"
      - "Uncaught ReferenceError"
      - "Failed to load module script"
      등.

### 7.3 캐시 헤더 검증

- [ ] HTML 응답 헤더에 캐시 정책이 있다. DevTools에서 HTML 요청의 응답 헤더 확인:
      ```
      Request: https://example.com/docs/page
      Response Headers:
      Cache-Control: no-cache, no-store, must-revalidate
      ```

- [ ] CSS/JS 응답 헤더에 장시간 캐시 정책이 있다:
      ```
      Request: https://example.com/assets/css/design-tokens.css?v=abc123de
      Response Headers:
      Cache-Control: public, max-age=31536000, immutable
      (또는 웹 서버 설정이 이를 제공)
      ```

- [ ] asset URL이 버전 쿼리를 포함한다(`?v=hash`).

### 7.4 보안 헤더 확인

- [ ] HTML 응답이 보안 헤더를 포함한다:
      ```
      X-Content-Type-Options: nosniff
      X-Frame-Options: DENY
      Content-Security-Policy: default-src 'self'
      ```
      DevTools Network tab에서 확인.

- [ ] 브라우저 콘솔에 CSP 위반 경고가 없다:
      - "Refused to load the script because it violates the Content Security Policy"
      등.

### 7.5 기본 기능 테스트

- [ ] 검색 기능(있으면): 검색어 입력 후 결과가 표시된다.
- [ ] 문서 생성/편집(있으면): 폼이 로드되고, 제출이 가능하다.
- [ ] 폼 유효성 검사(있으면): 빈 필드로 제출 시 오류 메시지가 표시된다.
- [ ] 링크 네비게이션: 각 링크를 클릭하면 해당 페이지가 로드된다(404 없음).

**자동화**: 배포 스크립트나 모니터링 도구가 위 확인을 자동으로 수행할 수 있다:
- Selenium/Playwright 같은 브라우저 automation으로 렌더링 확인
- curl/wget으로 HTTP header 검증
- 로그 모니터링으로 에러 감지

### 7.6 성능 기준 확인

- [ ] 첫 페이지 로드 시간이 합리적이다(3초 이내 권장).
      DevTools Performance tab 또는 Lighthouse에서 측정.

- [ ] 정적 asset 크기가 performance budget을 초과하지 않는다.
      task 0580에서 정의한 기준 따름. DevTools에서 asset size 확인.

## 8. 배포 후 지속적 모니터링 (Post-Deployment Monitoring)

배포 직후 며칠~주 동안 서비스 상태를 모니터링.

### 8.1 에러 로그 모니터링

- [ ] 웹 서버의 error log(`php_error.log`, `apache_error.log` 등)에서
      5xx 오류가 급증하지 않는다. 로그 경로는 shared hosting 제어판에서 확인.

- [ ] 특히 다음 오류가 없는지 확인:
      - "PHP Parse error": syntax error (배포 파일 손상)
      - "Fatal error: Class not found": 필수 파일 누락
      - "Permission denied": 파일 권한 문제

### 8.2 사용자 피드백

- [ ] 사용자들이 특정 페이지에서 오류를 보고하지 않는다.
- [ ] 검색/폼 기능이 정상 작동한다는 피드백.

### 8.3 자동 모니터링

- [ ] 정기적인 health check 스크립트 실행(매 5분/10분):
      ```bash
      curl -I https://example.com/
      curl -I https://example.com/assets/css/design-tokens.css
      # HTTP status 200 확인
      ```

- [ ] CDN/프록시를 거친다면, cache hit ratio 모니터링.
      정상이면 asset의 cache hit rate가 90% 이상.

## 9. 스킨(Skin) 확인 (Phase H: NamuWiki-style Skin, 0689-0694)

나무위키풍 스킨(상단바, 브랜드 색, 문서 액션 탭, 사이드바/반응형)이 배포
산출물에 빠짐없이 포함되고, 실제로 렌더링되는지 확인한다.
해당 태스크: 0689(design tokens/브랜드 색), 0690(상단 네비게이션 바),
0691(header/footer 통합), 0692(문서 헤더/액션 탭), 0693(대문 개편),
0694(사이드바/반응형), 0695(통합 QA/배포 패키지 갱신).

### 9.1 스킨 자산 배포 확인

- [ ] `php/public/assets/css/`의 스킨 CSS 파일(`design-tokens.css`,
      `navigation.css`, `layout.css`, `sidebar.css`, `document-header.css`,
      `front-page.css`, `buttons.css`, `print.css`, `responsive-table.css`)이
      모두 배포 패키지에 포함되었다. `php/deployment-package-manifest.json`의
      `php/public/**` include 패턴이 이 파일들을 포함하는지 확인:
      ```bash
      find php/public/assets/css -name '*.css'
      ```

- [ ] 갱신된 `php/src/Ui/**` 컴포넌트(`NavigationBar`, `Navigation`,
      `NavigationItem`, `Sidebar`, `DocumentHeader`, `DocumentActionTabs`,
      `FrontPage` 등)도 배포 패키지의 `php/src/**` include 패턴에 포함되었다.

**자동화**: `tests/test_php_deployment_package_manifest.py`의
`test_php_deployment_package_manifest_covers_skin_assets`가 현재 디스크의
스킨 CSS/Ui 파일 목록이 manifest include 패턴에 실제로 걸리는지 회귀
검사한다.

### 9.2 상단바 노출 확인

- [ ] 브라우저에서 홈(`/`)과 문서(`/wiki/{title}`) 페이지 모두 header에
      상단 네비게이션 바(`<nav class="site-nav">`, 브랜드 로고, 검색
      입력)가 노출된다.

**자동화**: `php/scripts/smoke-ui-skin.sh`(`UiSkinSmokeTest.php`)가 DB
없이 GET `/`, GET `/wiki/{title}` 응답에 `site-nav` 마크업이 있는지
확인한다. 라이브 배포본에서는 `php/scripts/live-e2e-smoke-test.sh`의
`skin_top_bar_and_brand_check` 시나리오가 동일하게 확인한다.

### 9.3 브랜드색 `#008485` 적용 확인

- [ ] `design-tokens.css`의 `--color-brand`가 `#008485`로 정의되어
      있고, 버튼/링크/네비게이션 활성 상태 등에 이 색이 실제로 적용된다
      (DevTools에서 계산된 스타일 확인).

**자동화**: `UiSkinSmokeTest.php`가 배포되는 `design-tokens.css` 파일
내용에서 `--color-brand: #008485;`를 직접 확인한다.
`live-e2e-smoke-test.sh`의 `skin_top_bar_and_brand_check` 시나리오가
라이브 배포본의 `design-tokens.css` asset을 GET해 같은 값을 확인한다.

### 9.4 문서 액션 탭 확인

- [ ] 문서 view 페이지(`/wiki/{title}`)에 읽기/편집/역사/토론 액션 탭
      (`<ul class="document-tabs">`)이 노출되고, 편집 탭이
      `/wiki/{title}/edit`로 이어진다.

**자동화**: `UiSkinSmokeTest.php`가 `/wiki/{title}` route 응답에
`document-tabs` 마크업이 있는지 확인한다. 라이브 배포본에서는
`live-e2e-smoke-test.sh`의 `skin_document_action_tabs_check` 시나리오가
관리자 세션으로 생성한 문서를 조회해 확인한다 — 관리자 자격 증명
(`SMOKE_ADMIN_USER`/`SMOKE_ADMIN_PASSWORD`)이 없으면 안전하게 skip한다.

### 9.5 반응형(Responsive) 확인

- [ ] 좁은 화면(모바일 뷰포트, 640px 이하)에서 사이드바가 접힘 토글
      메뉴로 전환되고, 데스크톱 폭에서는 고정 폭 컬럼으로 항상 펼쳐진다
      (`sidebar.css`의 `@media (max-width: 640px)`/`@media (min-width:
      641px)` 규칙).

**자동화**: `UiSkinSmokeTest.php`가 배포되는 `sidebar.css` 파일에
반응형 `@media (max-width: ...)` 규칙이 있는지 확인한다.
`live-e2e-smoke-test.sh`의 `skin_responsive_asset_check` 시나리오가
라이브 배포본의 `sidebar.css` asset을 GET해 같은 규칙을 확인한다.

## 10. 관리자 콘솔 확인 (Phase I: Admin console wiring, 0696-0702)

- [ ] 익명 사용자는 `/admin` 접근 시 `/login`으로 302되거나 403으로
      차단된다.
- [ ] 관리자 계정으로 로그인한 뒤 `/admin`, `/admin/maintenance`,
      `/admin/backup`, `/admin/restore`, `/admin/diagnostics`,
      `/admin/diagnostics/files`가 모두 200으로 열린다.
- [ ] 비관리자 계정은 관리자 하위 화면에서 403을 받는다.
- [ ] 상단바의 "관리" 링크는 관리자에게만 보이고 익명/비관리자에게는
      보이지 않는다.
- [ ] 배포 패키지에는 `php/src/**`와 `php/public/**`가 포함되어 관리자
      화면 컴포넌트와 CSS 자산이 누락되지 않는다
      (`php/deployment-package-manifest.json` 확인).

**자동화**: `php/tests/Http/AdminPhaseIRoutesTest.php`가 로컬에서
유지보수/백업/복원/진단 라우트의 관리자 게이트, CSRF, 위험 작업 확인,
유지보수 예외를 검증한다. 라이브 배포본에서는
`php/scripts/live-e2e-smoke-test.sh`의 `anonymous_admin_denied_check`와
`admin_console_routes_check` 시나리오가 관리자 콘솔 보호와 도달성을
확인한다. 관리자 자격 증명이 없으면 인증이 필요한 시나리오는 안전하게
skip한다.

## 11. Phase J 확인 (NamuMark 렌더 + 편집 UX + history/discussion, 0704-0712)

위키 문법(NamuMark) 렌더링, 편집 화면의 요약/미리보기/툴바/문법 도움말,
문서별 history/discussion이 배포 산출물에 빠짐없이 포함되고, 실제로
동작하는지 확인한다. 해당 태스크: 0704(inline parser), 0705(block
parser), 0706(renderer/view 통합), 0707(편집 요약 필드), 0708(편집
미리보기), 0709(편집 툴바/문법 도움말), 0710(history route), 0711
(discussion persistence), 0712(discussion route), 0713(통합 QA/배포
패키지 갱신).

### 11.1 Phase J 자산 배포 확인

- [ ] `php/public/assets/css/document-content.css`(문서 본문/표/TOC
      스타일), `php/public/assets/css/editor-toolbar.css`(편집 툴바/문법
      도움말 스타일)이 배포 패키지에 포함되었다.
- [ ] `php/public/assets/js/edit-preview.js`(미리보기 fetch 갱신),
      `php/public/assets/js/edit-toolbar.js`(툴바 버튼 문법 삽입)이
      배포 패키지에 포함되었다. `php/deployment-package-manifest.json`의
      `php/public/**` include 패턴이 이 JS 파일들을 포함하는지 확인:
      ```bash
      find php/public/assets/js -name '*.js'
      ```
- [ ] 갱신된 `php/src/Modules/Parser/**`, `php/src/Modules/Render/**`
      (NamuMark 파서/렌더러), `php/src/Modules/Discussion/**`,
      `php/src/Modules/Revision/**`(history/discussion 저장소)도 배포
      패키지의 `php/src/**` include 패턴에 포함되었다.

**자동화**: `tests/test_php_deployment_package_manifest.py`의
`test_php_deployment_package_manifest_covers_phase_j_assets`가 현재
디스크의 Phase J JS 자산과 도메인 모듈 파일 목록이 manifest include
패턴에 실제로 걸리는지 회귀 검사한다.

### 11.2 NamuMark 렌더 확인

- [ ] `/wiki/{title}`가 저장된 위키 문법을 실제 HTML로 렌더링한다:
      굵게(`'''텍스트'''` → `<strong>`), 내부 링크(`[[문서]]` → `<a
      href="/wiki/...">`), 표(`||셀||셀||` → `<table>`), 제목(`==
      제목 ==` → `<h2>` 등)이 원문 그대로가 아니라 실제 마크업으로
      나타난다.
- [ ] 문서에 제목이 2개 이상이면 본문 위에 목차(TOC, `<nav
      class="toc">`)가 함께 렌더링된다.

**자동화**: `php/tests/Http/DocumentViewNamuMarkRouteTest.php`가 route
수준에서, `php/tests/Http/UiPhaseJSmokeTest.php`
(`php/scripts/smoke-ui-phase-j.sh`)가 DB 없이 컴포넌트 수준에서 굵게/
링크/표/TOC 렌더링을 확인한다. 라이브 배포본에서는
`php/scripts/live-e2e-smoke-test.sh`의 `phase_j_namumark_render_check`
시나리오가 실제로 생성한 문서의 렌더된 HTML에서 `<strong>`/`<table>`/
`<nav class="toc"` 마크업을 확인한다.

### 11.3 편집 화면 확인

- [ ] `/wiki/{title}/edit` 화면에 편집 요약 입력(`<label
      for="summary">`), 저장 전 미리보기 영역(`class="edit-preview"`),
      NamuMark 문법 삽입 툴바(`class="editor-toolbar"`), 접이식 문법
      도움말(`class="editor-help"`)이 모두 나타난다.
- [ ] `assets/js/edit-preview.js`/`assets/js/edit-toolbar.js`가 로드되면
      미리보기 버튼과 툴바 버튼이 페이지 새로고침 없이 동작한다(JS
      없이도 각각 `/preview` 폼 제출과 원문 직접 입력으로 대체된다).

**자동화**: `php/tests/Http/EditSummaryFieldTest.php`,
`php/tests/Http/DocumentEditPreviewRouteTest.php`가 route 수준에서,
`php/tests/Http/UiPhaseJSmokeTest.php`가 DB 없이 컴포넌트 수준에서
편집 화면 마크업을 확인한다. 라이브 배포본에서는
`live-e2e-smoke-test.sh`의 `phase_j_edit_ux_check` 시나리오가 관리자
세션으로 연 편집 폼 응답에서 같은 마크업을 확인한다 — 관리자 자격
증명이 없으면 안전하게 skip한다.

### 11.4 history 확인

- [ ] `GET /wiki/{title}/history`가 200으로 응답하고, 문서의 리비전
      목록(작성자/시각/편집 요약)을 시간 내림차순으로 보여준다.

**자동화**: `php/tests/Http/DocumentHistoryDiffRouteTest.php`가 route
수준에서, `php/tests/Http/UiPhaseJSmokeTest.php`가 DB 없이
`DocumentHistoryPage` 렌더링을 확인한다. 라이브 배포본에서는
`live-e2e-smoke-test.sh`의 `phase_j_history_route_check` 시나리오가
실제 배포본의 history 경로 응답 상태(200 또는 접근 제어에 따른
302/403)를 확인한다.

### 11.5 discussion 확인

- [ ] `GET /wiki/{title}/discussion`이 200으로 응답하고, 문서의 토론
      스레드/댓글 목록과 새 스레드 작성 form을 보여준다.
- [ ] 로그인한 사용자가 `POST /wiki/{title}/discussion`으로 새 스레드를,
      `POST /wiki/{title}/discussion/{threadId}/comment`로 댓글을 실제로
      작성할 수 있다.

**자동화**: `php/tests/Http/DiscussionRouteTest.php`가 route 수준에서,
`php/tests/Http/UiPhaseJSmokeTest.php`가 DB 없이 스레드/댓글 생성과
`DiscussionPage` 렌더링을 확인한다. 라이브 배포본에서는
`live-e2e-smoke-test.sh`의 `phase_j_discussion_route_check`(읽기),
`phase_j_discussion_write_check`/`phase_j_comment_write_check`(스레드/
댓글 작성)가 확인한다 — 관리자 자격 증명이 없으면 쓰기 시나리오는
안전하게 skip한다.

## 12. 이 체크리스트가 다루지 않는 것

- Database 마이그레이션이나 초기화 — DB phase checklist 참고 (0411 이후)
- PHP 런타임 버전/확장 설정 — runtime phase checklist 참고 (0396)
- 보안 감사 범위(penetration test, code review 등) — 별도 security audit
- 성능 최적화(CDN, cache warming, query optimization 등) — performance tuning phase
- 운영 자동화(배포 스크립트, 백업, 모니터링 alert 등) — DevOps/infrastructure phase

## 관련 문서

- [PHP UI Architecture](php-ui-architecture.md) — Phase D 전체 UI 아키텍처 원본
- [PHP Static Asset Serving](php-static-asset-serving.md) — asset 배포 위치와 웹 서버 설정
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md) — HTML과 asset 캐시 정책 구분
- [PHP UI Static Asset Integrity Policy](php-ui-static-asset-integrity.md) — 버전/해시 기반 캐시 무효화
- [DB Web Hosting Constraints](db-web-hosting-constraints.md) — shared hosting 환경 제약
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 전체 배포 환경 정책
- [PHP Runtime Phase QA Checklist](php-runtime-phase-qa-checklist.md) — Phase B QA 체크리스트
- [DB Phase QA Checklist](db-phase-qa-checklist.md) — Phase C QA 체크리스트
- [PHP, ANSI DB, UI micro job prompts 0351-0670](php-db-ui-micro-job-prompts-0351-0670.md) — Phase D(0521-0610) 전체 태스크 목록
