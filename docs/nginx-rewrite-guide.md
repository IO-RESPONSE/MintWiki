# Nginx Rewrite Guide

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서 (태스크 0614).

이 문서는 Nginx를 사용하는 VPS 또는 관리형 호스팅 환경에서
이 애플리케이션의 **front controller 패턴**을 동작시키기 위해
필요한 Nginx 설정을 제공한다.

Apache `.htaccess` 기반 설정은 `docs/shared-hosting-target-baseline.md` § 3.2 참고.
VPS 운영자가 Nginx 설정을 구성하려면 이 문서를 따른다.

## 목적과 범위

- **대상**: VPS 또는 관리형 호스팅의 운영자, Nginx 설정 담당자.
- **다루는 것**:
  - Front controller 패턴을 Nginx에서 구현하는 방식
  - `try_files` 지시문을 사용한 URL rewrite 설정
  - PHP-FPM 통합 설정
  - 정적 자산(asset) 서빙 최적화

- **다루지 않는 것**:
  - SSL/TLS 설정 (Let's Encrypt 등) — 별도 운영 문서에서 다룬다.
  - 성능 튜닝(Nginx worker, PHP-FPM pool) — 별도 운영 가이드에서 다룬다.
  - 로드 밸런싱 또는 리버스 프록시 — 구성의 복잡도에 따라 별도 문서 필요.

## 1. 핵심 개념

### 1.1 Front Controller 패턴이란?

이 애플리케이션은 **모든 HTTP 요청을 `index.php`로 라우팅**하는
front controller 패턴을 사용한다.

```
사용자 요청: GET /documents/123
     ↓
     [Nginx rewrite]
     ↓
실제 실행: GET /index.php?path=/documents/123
     ↓
[PHP 라우터가 path를 파싱하여 적절한 컨트롤러 호출]
```

Apache에서는 `.htaccess`의 `RewriteRule`로 이를 구현하고(`docs/shared-hosting-target-baseline.md` § 3.2),
**Nginx에서는 `try_files` 지시문**으로 구현한다.

### 1.2 Nginx vs. Apache의 차이

| 항목 | Apache | Nginx |
|---|---|---|
| 설정 파일 | `.htaccess` (디렉터리별) | `nginx.conf` (중앙집중식) |
| Rewrite 엔진 | `mod_rewrite` + RegEx | `try_files` (더 간단함) |
| 성능 | 디렉터리별 파싱 오버헤드 | 높은 성능 |
| 설정 위치 | 각 디렉터리 | 서버 관리자가 중앙에서 관리 |

Nginx는 요청 처리 시점에 설정을 재읽지 않으므로, 변경 후 `nginx -s reload` 명령으로
설정을 다시 로드해야 한다.

## 2. Nginx 설정 (VPS 기본 패턴)

### 2.1 최소 설정

다음은 이 애플리케이션을 Nginx + PHP-FPM에서 실행하는 **최소 설정**이다.

호스팅 제공자의 Nginx 설정 디렉터리(보통 `/etc/nginx/sites-available/` 또는
`/etc/nginx/conf.d/`)에 다음과 같은 파일을 생성한다:

```nginx
# /etc/nginx/sites-available/example.com 또는 /etc/nginx/conf.d/example.conf
# 또는 호스팅 제어판에서 "Nginx configuration" 섹션에 붙여넣는다.

server {
    listen 80;
    server_name example.com www.example.com;

    # 문서 루트: 애플리케이션의 php/public 디렉터리
    root /var/www/example.com/php/public;
    index index.php;

    # 로그 위치 (호스팅별로 다를 수 있음)
    access_log /var/log/nginx/example.com_access.log;
    error_log /var/log/nginx/example.com_error.log;

    # 1. 정적 자산(CSS, JS, 이미지 등)은 직접 서빙한다.
    #    존재하지 않는 파일/디렉터리면 front controller로 전달한다.
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    # 2. .php 파일 요청을 PHP-FPM에 전달한다.
    location ~ \.php$ {
        # PHP-FPM이 로컬 소켓에서 대기 중인 경우 (권장):
        fastcgi_pass unix:/run/php-fpm.sock;
        
        # 또는 TCP 포트에서 대기 중인 경우:
        # fastcgi_pass 127.0.0.1:9000;

        # PHP 스크립트의 실제 파일 경로를 전달한다.
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;

        # PHP-FPM 표준 파라미터들을 포함한다.
        include fastcgi_params;
    }

    # 3. .htaccess 파일 같은 설정 파일은 직접 접근을 방지한다.
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### 2.2 설정 설명

#### 2.2.1 `location / { try_files ... }`

```nginx
location / {
    try_files $uri $uri/ /index.php?$query_string;
}
```

이 지시문은 **요청된 URI를 순서대로 확인**하고, 다음과 같이 처리한다:

1. **`$uri`**: 요청된 정확한 파일이 존재하는가?
   - 예: `GET /assets/style.css` → `/var/www/example.com/php/public/assets/style.css` 확인
   - 존재하면 **그 파일을 서빙하고 종료**

2. **`$uri/`**: 요청된 경로가 **디렉터리**인가?
   - 예: `GET /documents/` → `/var/www/example.com/php/public/documents/` 확인
   - 존재하면 해당 디렉터리의 `index.php` 서빙

3. **`/index.php?$query_string`**: 위 둘 다 아니면 front controller로 전달
   - 예: `GET /documents/123` → `/index.php?/documents/123` 실행
   - PHP 애플리케이션이 `REQUEST_URI` 환경변수에서 경로를 읽고 라우팅 수행

#### 2.2.2 PHP-FPM 연결

```nginx
location ~ \.php$ {
    fastcgi_pass unix:/run/php-fpm.sock;
    # 또는
    # fastcgi_pass 127.0.0.1:9000;
}
```

- **Unix 소켓** (`unix:/run/php-fpm.sock`): 권장 (더 빠르고 오버헤드 적음)
- **TCP 포트** (`127.0.0.1:9000`): 로컬 개발 또는 분산 설정 시 사용

호스팅 제공자의 기본 설정을 따른다. `systemctl status php-fpm` 또는
호스팅 패널에서 확인할 수 있다.

#### 2.2.3 숨김 파일/디렉터리 차단

```nginx
location ~ /\. {
    deny all;
}
```

`.htaccess`, `.env`, `.git` 같은 설정 파일을 외부에서 접근하지 못하도록 차단한다.

### 2.3 설정 적용 및 테스트

#### 2.3.1 설정 검증

```bash
# 문법 오류가 없는지 확인한다.
sudo nginx -t
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

#### 2.3.2 설정 재로드

```bash
# Nginx 프로세스를 재시작하지 않고 설정만 다시 로드한다.
sudo systemctl reload nginx
# 또는
sudo nginx -s reload
```

#### 2.3.3 동작 확인

```bash
# 1. Front controller 패턴이 동작하는지 확인
curl https://example.com/documents/123
# 404가 아니라 애플리케이션의 응답(HTML 또는 JSON)이 반환되어야 한다.

# 2. 정적 자산이 올바르게 서빙되는지 확인
curl -I https://example.com/assets/style.css
# HTTP/1.1 200 OK
# Content-Type: text/css
# ... 등이 출력되어야 한다.

# 3. 로그 확인
tail -f /var/log/nginx/example.com_access.log
tail -f /var/log/nginx/example.com_error.log
```

## 3. 고급 설정

### 3.1 HTTP to HTTPS 리다이렉트

```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com www.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    root /var/www/example.com/php/public;
    index index.php;

    # ... 나머지 설정은 동일
}
```

### 3.2 `X-Forwarded-For` 헤더 설정 (리버스 프록시 환경)

로드 밸런서 또는 리버스 프록시 뒤에 있는 경우, 클라이언트 IP를 올바르게 전달해야 한다:

```nginx
location ~ \.php$ {
    fastcgi_pass unix:/run/php-fpm.sock;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    
    # 리버스 프록시에서 전달된 클라이언트 IP를 사용한다.
    fastcgi_param HTTP_X_FORWARDED_FOR $proxy_add_x_forwarded_for;
    fastcgi_param HTTP_X_FORWARDED_PROTO $scheme;
    fastcgi_param HTTP_X_FORWARDED_HOST $server_name;

    include fastcgi_params;
}
```

### 3.3 Gzip 압축 활성화

응답 크기를 줄이기 위해 gzip 압축을 활성화한다:

```nginx
server {
    # ... 기본 설정

    gzip on;
    gzip_types text/css text/javascript application/json application/javascript;
    gzip_min_length 1000;
}
```

### 3.4 캐시 헤더 설정

정적 자산의 브라우저 캐시를 제어한다:

```nginx
server {
    # ... 기본 설정

    # CSS, JS, 이미지 캐시 (1년)
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # HTML 캐시하지 않음 (항상 최신 버전 로드)
    location ~ \.html?$ {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
```

## 4. 호스팅 제공자별 설정

### 4.1 DigitalOcean, Linode, Vultr (표준 VPS)

위의 **2.1 최소 설정**을 사용한다.

```bash
# 호스팅 제어판 또는 SSH로 접근하여:
sudo nano /etc/nginx/sites-available/example.com
# 내용 붙여넣기, 저장

sudo ln -s /etc/nginx/sites-available/example.com \
         /etc/nginx/sites-enabled/example.com
sudo nginx -t
sudo systemctl reload nginx
```

### 4.2 Plesk (관리형 호스팅)

Plesk 제어판에서:

1. **Domains** → 도메인 선택 → **Hosting Settings**
2. **Web Server** 섹션에서 **"Nginx"** 선택 (또는 **"Apache and Nginx"**)
3. **Additional nginx directives** 또는 **"Nginx Configuration"** 항목에 다음을 붙여넣는다:

```nginx
location / {
    try_files $uri $uri/ /index.php?$query_string;
}

location ~ \.php$ {
    fastcgi_pass 127.0.0.1:9000;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    include fastcgi_params;
}
```

4. 저장 후 Nginx 재로드 (Plesk가 자동 처리)

### 4.3 cPanel/WHM (Nginx 플러그인)

cPanel에 **EasyApache 4** 또는 **CloudLinux LVE Manager**가 설치된 경우:

1. **WHM** → **EasyApache 4** 또는 **Home** → **Domains**
2. 도메인별 Nginx 설정을 활성화
3. 위의 설정을 적용 (cPanel UI 또는 직접 파일 편집)

## 5. 문제 해결

### 5.1 "404 Not Found" 또는 "File not found"

**증상**: 실제 파일이 아닌 경로(예: `/documents/123`)에 접근할 때 404 반환

**원인**:
- `try_files` 지시문이 올바르게 설정되지 않음
- 문서 루트(root)가 잘못됨

**해결**:
```bash
# 1. 문서 루트 확인
ls -la /var/www/example.com/php/public/
# index.php가 있는지 확인

# 2. Nginx 설정 확인
sudo nginx -t
# 오류가 없는지 확인

# 3. 로그 확인
sudo tail -f /var/log/nginx/example.com_error.log
# 오류 메시지 확인
```

### 5.2 PHP 파일이 다운로드됨 (실행되지 않음)

**증상**: `.php` 파일에 접근하면 파일이 다운로드됨

**원인**:
- PHP-FPM이 실행 중이지 않음
- `fastcgi_pass` 설정이 잘못됨

**해결**:
```bash
# 1. PHP-FPM 상태 확인
sudo systemctl status php-fpm
# Active: active (running) 이어야 함

# 2. PHP-FPM 소켓/포트 확인
sudo netstat -tlnp | grep -i fpm
# Unix 소켓 또는 TCP 포트가 대기 중이어야 함

# 3. 설정에서 fastcgi_pass 값을 위의 소켓/포트와 일치시킨다.
```

### 5.3 PHP 변수(`$_GET`, `$_POST` 등)가 비어 있음

**증상**: PHP에서 `$_GET`, `$_POST`, `$_SERVER['REQUEST_URI']` 등이 비어 있음

**원인**:
- `fastcgi_param` 설정이 불완전함

**해결**:
```nginx
location ~ \.php$ {
    fastcgi_pass unix:/run/php-fpm.sock;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    
    # 다음을 반드시 포함한다:
    include fastcgi_params;
    
    # 또는 필요한 파라미터를 명시적으로 설정:
    fastcgi_param REQUEST_METHOD $request_method;
    fastcgi_param QUERY_STRING $query_string;
    fastcgi_param REQUEST_URI $request_uri;
}
```

### 5.4 HTTPS 연결 실패

**증상**: `https://example.com`에 접속할 수 없거나 인증서 오류

**원인**:
- Let's Encrypt 인증서가 설치되지 않음
- Nginx 설정에서 SSL 파일 경로가 잘못됨

**해결**:
```bash
# Let's Encrypt 인증서 설치 (Certbot)
sudo apt update && sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d example.com -d www.example.com
# 인증서가 /etc/letsencrypt/live/example.com/에 생성됨

# Nginx 설정에서 다음을 확인:
# ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
```

## 6. 성능 및 보안

### 6.1 Nginx 성능

Nginx는 Apache보다 메모리 사용량이 적고 요청 처리가 빠르다.
기본 설정으로도 충분한 성능을 제공한다.

추가 튜닝이 필요한 경우는 운영 문서(`docs/nginx-performance-tuning.md`)를 참고한다(Phase F).

### 6.2 보안

- **X-Frame-Options** 헤더: Clickjacking 방지
- **X-Content-Type-Options** 헤더: MIME 스니핑 방지
- **Referrer-Policy** 헤더: 레퍼러 정보 제어

이들은 PHP 애플리케이션 수준에서 설정하는 것을 권장한다
(docs/php-security-headers.md`).

## 7. 배포 체크리스트

새로운 Nginx 호스팅에 이 애플리케이션을 배포할 때:

- [ ] **Nginx 버전 확인**: 1.16 이상 (대부분의 VPS는 이 이상)
  ```bash
  nginx -v
  ```

- [ ] **PHP-FPM 실행**: PHP 8.1 이상, PHP-FPM 활성화
  ```bash
  php -v
  systemctl status php-fpm
  ```

- [ ] **문서 루트 준비**: `php/public` 디렉터리 배포 및 권한 설정
  ```bash
  chmod -R 755 /var/www/example.com/php/public
  ```

- [ ] **Nginx 설정 적용**: 위의 최소 설정 또는 호스팅별 설정 사용
  ```bash
  sudo nginx -t && sudo systemctl reload nginx
  ```

- [ ] **동작 확인**: 브라우저에서 다음 접속 테스트
  - `https://example.com` (홈페이지)
  - `https://example.com/documents/123` (존재하지 않는 경로 → 앱 응답)
  - `https://example.com/assets/style.css` (정적 자산 → 200 OK)

- [ ] **로그 확인**: 오류가 없는지 확인
  ```bash
  sudo tail -20 /var/log/nginx/example.com_error.log
  ```

## 관련 문서

- `docs/shared-hosting-target-baseline.md` — 공용 호스팅 요구사항 및 Apache 설정
- `docs/php-static-asset-serving.md` — 정적 자산 서빙 방식
- `docs/php-ui-cache-header-policy.md` — HTTP 캐시 헤더 정책
- `docs/db-web-hosting-constraints.md` — 데이터베이스 제약 사항
- 태스크 0613 — `.htaccess` (Apache) 구현
