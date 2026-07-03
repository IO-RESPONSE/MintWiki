# Public Docroot Policy

**Phase E: Shared Hosting Packaging and Installer, 0611-0670** 문서.
[Shared Hosting Target Baseline](shared-hosting-target-baseline.md)을 기반으로,
웹 서버의 document root로 노출할 디렉토리 구조와 보안 분리 원칙을 정의한다.

## 목적

공용 웹호스팅에 배포할 때, 애플리케이션 설정(config), 데이터베이스 스키마,
소스 코드, 테스트 파일 등이 웹 브라우저를 통해 접근되면 안 된다.
이 문서는 다음을 정의한다:

- **공개 디렉토리** (`public/`): 웹 서버의 document root로 설정할 유일한 디렉토리
- **비공개 디렉토리** (`src/`, `vendor/`, `config/`, `storage/` 등): 웹 서버가 접근할 수 없어야 하는 디렉토리
- **웹 서버 설정**: 공개 디렉토리만 document root로 설정하는 방식
- **파일 접근 제어**: document root 외부 파일에 접근하는 메커니즘

## 적용 범위

- 공용 웹호스팅(cPanel, Plesk, DirectAdmin 등)에 배포된 PHP 애플리케이션
- 단일 도메인 배포 (MintWiki 인스턴스 하나 = 하나의 호스팅 계정)
- Apache 또는 Nginx를 사용하는 표준 웹 호스팅

적용되지 않는 것:

- 개발 환경 (로컬 개발자는 프로젝트 루트를 document root로 설정할 수 있음)
- 전용 서버(dedicated server) 또는 Docker/Kubernetes 환경 (다른 배포 전략 사용)
- 다중 도메인 호스팅 (여러 애플리케이션을 호스팅하는 경우)

## 1. 디렉토리 구조

### 1.1 배포 구조

호스팅에 배포될 때의 디렉토리 구조:

```
/home/user/public_html/           ← 호스팅 계정 루트 (document root 아님)
├── public/                        ← 웹 서버 document root (이 디렉토리만 노출)
│   ├── index.php                  ← Front controller
│   ├── assets/                    ← Static CSS/JS/images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── robots.txt                 ← 로봇 제외 규칙 (정적 파일 또는 front controller로 서빙)
├── src/                           ← PHP 소스 코드 (비공개)
│   ├── App/
│   ├── Http/
│   ├── Modules/
│   ├── Ui/
│   ├── Persistence/
│   ├── Security/
│   └── Installer/
├── vendor/                        ← Composer 의존성 (비공개)
│   └── (자동 생성)
├── config/                        ← 설정 파일 (비공개)
│   ├── config.php
│   ├── local-config.php           ← 호스팅별 로컬 설정
│   └── database.php
├── storage/                       ← 런타임 생성 파일 (비공개)
│   ├── cache/
│   ├── uploads/
│   ├── backup/
│   └── logs/
├── db/                            ← 스키마 정의 (비공개)
│   ├── schema.sql
│   └── migrations/
├── tests/                         ← 테스트 파일 (비공개)
│   ├── Unit/
│   ├── Integration/
│   └── Feature/
├── scripts/                       ← 관리 스크립트 (비공개)
│   ├── test.sh
│   ├── qa.sh
│   └── build.sh
├── docs/                          ← 문서 (비공개)
│   ├── php-ui-cache-header-policy.md
│   ├── public-docroot-policy.md
│   └── (이 파일)
├── composer.json                  ← 의존성 정의 (비공개)
├── composer.lock                  ← 의존성 잠금 (비공개)
├── README.md                      ← 프로젝트 설명 (비공개)
└── .gitignore                     ← Git 설정 (비공개)
```

### 1.2 웹 서버가 노출하는 것

웹 서버(Apache/Nginx)의 document root는 **`public/` 디렉토리만**으로 설정한다:

```
# Apache httpd.conf 또는 호스팅 패널 설정
DocumentRoot /home/user/public_html/public

# 또는 Nginx
root /home/user/public_html/public;
```

이렇게 하면 외부에서 접근 가능한 경로:

```
https://example.com/                           → public/index.php
https://example.com/assets/css/app.css        → public/assets/css/app.css
https://example.com/robots.txt                → public/robots.txt (정적 파일 또는 front controller)
https://example.com/documents                 → public/index.php (라우팅)
```

외부에서 **절대 접근할 수 없는** 경로:

```
https://example.com/src/                      ❌ 접근 불가 (document root 외부)
https://example.com/config/                   ❌ 접근 불가 (document root 외부)
https://example.com/vendor/                   ❌ 접근 불가 (document root 외부)
https://example.com/storage/                  ❌ 접근 불가 (document root 외부)
https://example.com/composer.json             ❌ 접근 불가 (document root 외부)
```

## 2. 각 디렉토리의 역할과 보안 분류

| 디렉토리 | 내용 | 웹 접근 | 이유 |
|---|---|---|---|
| `public/` | Front controller, static assets | ✓ 필요 | 웹 서버 document root |
| `src/` | PHP 소스 코드 | ❌ 금지 | 소스 공개 및 수정 방지 |
| `vendor/` | 제3자 라이브러리 | ❌ 금지 | 보안 취약점 노출 방지 |
| `config/` | DB 자격증명, 애플리케이션 설정 | ❌ 금지 | 민감한 정보 보호 |
| `storage/` | 사용자 업로드, 캐시, 로그 | ❌ 금지 | 시스템 파일 보호 |
| `db/` | 스키마, 마이그레이션 | ❌ 금지 | DB 구조 노출 방지 |
| `tests/` | 테스트 코드 | ❌ 금지 | 테스트 우회 방지 |
| `docs/` | 개발 문서 | ❌ 금지 | 불필요한 정보 노출 방지 |

## 3. Front Controller를 통한 간접 접근

`public/` 디렉토리 외부의 파일에 접근하려면, **반드시 front controller(`public/index.php`)를 거쳐야 한다.**

### 3.1 Front Controller 구조

```php
// public/index.php
<?php
// 프로젝트 루트를 기준으로 src/ 로드
require_once __DIR__ . '/../vendor/autoload.php';
require_once __DIR__ . '/../config/config.php';

$app = new MintWiki\App\Application(
    new MintWiki\App\ConfigLoader(),
);

$response = $app->handle(
    MintWiki\Http\Request::fromGlobals()
);

$response->send();
```

모든 HTTP 요청(`GET /documents`, `POST /api/comments` 등)은 `public/index.php`를 거쳐 라우팅된다.

### 3.2 파일 포함(require) 메커니즘

`public/index.php`에서 상대 경로(`__DIR__ . '/../src/'` 등)를 사용하여 document root 외부 파일을 로드한다.

```php
// 안전한 방식: 상대 경로로 정확한 파일 참조
require_once __DIR__ . '/../src/Http/Router.php';
require_once __DIR__ . '/../vendor/autoload.php';
```

이 방식은:
- 웹 브라우저로는 직접 접근 불가 (document root 외부)
- PHP 스크립트(front controller)에서만 로드 가능

### 3.3 저장소(storage/) 접근

사용자 업로드, 캐시, 로그는 `storage/` 디렉토리에 저장되지만, 웹 브라우저에서 접근하려면:

```php
// src/Http/StorageHandler.php (예시)
public function handle(Request $request): Response
{
    // URL: GET /downloads/file-123.pdf
    // 실제 파일: storage/uploads/file-123.pdf
    
    $filePath = __DIR__ . '/../../storage/uploads/file-123.pdf';
    
    if (!file_exists($filePath)) {
        return Response::notFound();
    }
    
    // 접근 권한 확인
    if (!$this->auth->canAccess($filePath)) {
        return Response::forbidden();
    }
    
    // 파일 스트리밍
    return Response::file($filePath, 'application/pdf');
}
```

이 방식으로:
- 개별 파일 접근 권한 확인 가능
- 파일 목록 열람 방지 (directory listing 불가)
- 호스팅 설정으로 한 번 더 차단 (`deny from all`)

## 4. 웹 서버 설정

### 4.1 Apache 설정 (호스팅 패널)

대부분의 공용 호스팅(cPanel, Plesk)에서는 호스팅 패널의 GUI로 document root를 설정한다.

**cPanel 예시**:
1. "Addon Domains" 또는 "Domains" 섹션
2. 도메인 추가/편집
3. **Document Root**: `/public_html/public` (기본값: `/public_html`)

**Plesk 예시**:
1. Domains 메뉴
2. 도메인 선택 → Hosting Settings
3. **Document Root**: `/domains/example.com/public` (기본값: `/domains/example.com/public_html`)

### 4.2 Apache 수동 설정 (전용 서버 또는 VPS)

호스팅사에서 document root 변경을 허용하지 않으면, Apache `.htaccess`로 우회할 수 있다:

```apache
# /home/user/public_html/.htaccess
# public/ 디렉토리를 실제 document root처럼 동작하게 함

RewriteEngine On
RewriteBase /

# public/ 디렉토리로 모든 요청 리다이렉트
RewriteCond %{REQUEST_URI} !^/public/
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /public/$1 [L]
```

**하지만 권장하지 않음**: 설정이 복잡하고, 실제 document root는 여전히 부모 디렉토리임.

**권장 방식**: 호스팅사 기술 지원에 문의하여 document root를 `public/`으로 설정하도록 요청.

### 4.3 Nginx 설정

호스팅사에서 Nginx를 사용하면:

```nginx
# /etc/nginx/conf.d/example.com.conf 또는 호스팅사 설정
server {
    server_name example.com;
    root /home/user/public_html/public;
    
    index index.php;
    
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

`root` 지시문을 `/home/user/public_html/public`으로 설정하면 된다.

### 4.4 웹 서버가 public/ 외부에 접근하지 못하도록 차단

설정 오류 시에도 보안을 유지하기 위해, `public/` 디렉토리 외부에 대한 접근을 명시적으로 차단한다:

**Apache (.htaccess in public/)**:

```apache
# public/.htaccess
# public/ 내 파일들의 기본 규칙
<FilesMatch "\.php$">
    SetHandler application/x-httpd-php
</FilesMatch>

# 부모 디렉토리 접근 시도 방지
RewriteEngine On
RewriteCond %{REQUEST_URI} \.\. [OR]
RewriteCond %{REQUEST_URI} /\.\. 
RewriteRule ^ - [F]
```

**Nginx**:

```nginx
# Nginx는 document root 설정만으로 충분
# 잘못된 경로는 자동으로 404를 반환함
location ~ /\.\. {
    deny all;
}
```

**파일 시스템 권한**:

```bash
# 호스팅 계정에서 권한 설정
chmod 750 /home/user/public_html       # 소유자만 접근
chmod 755 /home/user/public_html/public # 웹 서버(Apache/Nginx)도 읽을 수 있음
chmod 600 /home/user/public_html/config/*.php # 설정 파일 읽기만 가능
chmod 600 /home/user/public_html/composer.json # 의존성 파일 읽기만 가능
```

## 5. 특수한 파일들

### 5.1 robots.txt

`robots.txt`는 SEO 규칙을 정의하는 파일이며, 웹 루트(`/robots.txt`)에서 서빙되어야 한다.

#### 옵션 1: 정적 파일 (권장)

```
/public/robots.txt
```

웹 서버가 정적 파일로 직접 서빙한다:

```
GET https://example.com/robots.txt → public/robots.txt (200 OK)
```

장점:
- 웹 서버가 직접 서빙하므로 PHP 오버헤드 없음
- 캐싱 용이
- 간단한 구성

#### 옵션 2: Front Controller로 동적 생성

```php
// public/index.php에서 라우팅
if ($request->path() === '/robots.txt') {
    return $handler->handle('/robots.txt');
}
```

Front controller에서 `/robots.txt` 요청을 처리하여 동적으로 생성한다:

```php
// src/Http/RobotsTxtHandler.php
public function handle(Request $request): Response
{
    $content = <<<TXT
    User-Agent: *
    Disallow: /admin/
    Disallow: /api/
    Allow: /documents/
    TXT;
    
    return Response::text($content);
}
```

장점:
- 환경에 따라 다른 규칙 적용 가능
- 설정 파일에서 관리 가능

### 5.2 .htaccess (Apache 호스팅)

`.htaccess`는 Apache 서버 설정을 document root 내에서 제어하는 파일이다.

**위치**: `public/.htaccess`

```apache
# 모든 요청을 front controller로 라우팅
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    
    # 정적 파일과 디렉토리는 그냥 서빙
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    
    # 나머지는 front controller로
    RewriteRule ^ index.php [L]
</IfModule>
```

`.htaccess`는 document root 내에만 배치하며, document root 외부의 파일에 영향을 주지 않는다.

### 5.3 web.config (IIS 호스팅)

Windows/IIS 호스팅인 경우:

**위치**: `public/web.config`

```xml
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="RewriteToFront" stopProcessing="true">
                    <match url="^.*$" />
                    <conditions>
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="index.php" />
                </rule>
            </rules>
        </rewrite>
    </system.webServer>
</configuration>
```

## 6. 로컬 개발 환경 설정

개발자의 로컬 머신에서는 document root를 어디로 설정할지 선택할 수 있다:

### 6.1 공용 호스팅 환경 재현 (권장)

호스팅 환경과 동일하게 `public/`을 document root로 설정한다.

**Apache (XAMPP/MAMP)**:

```apache
# httpd.conf
DocumentRoot "/path/to/project/public"
<Directory "/path/to/project/public">
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
```

**Nginx (로컬)**:

```nginx
server {
    server_name localhost;
    root /path/to/project/public;
    
    index index.php index.html;
    
    location ~ \.php$ {
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

**PHP 내장 서버**:

```bash
# 프로젝트/public 디렉토리에서 실행
cd /path/to/project/public
php -S localhost:8000
```

장점:
- 공용 호스팅과 정확히 같은 구조
- 배포 전에 구조 검증 가능

### 6.2 프로젝트 루트를 document root로 설정 (편의상)

개발 초기 단계에는 프로젝트 루트 전체를 document root로 설정할 수 있다:

```apache
DocumentRoot "/path/to/project"
```

이 경우 `src/`, `config/` 등이 웹으로 접근 가능하지만, **배포하기 전에 `public/`으로 변경해야 한다.**

### 6.3 로컬 composer 스크립트

```json
{
    "scripts": {
        "serve": "php -S localhost:8000 -t public/",
        "serve-root": "php -S localhost:8000"
    }
}
```

실행:

```bash
composer serve     # public/ document root (권장)
composer serve-root # 프로젝트 루트 (개발 전용)
```

## 7. 테스트 전략

### 7.1 구조 검증 (unit test)

디렉토리 구조가 정책을 따르는지 확인한다.

```php
// php/tests/PublicDocrootTest.php
namespace MintWiki\Tests;

use PHPUnit\Framework\TestCase;

final class PublicDocrootTest extends TestCase
{
    private string $projectRoot;
    
    protected function setUp(): void
    {
        $this->projectRoot = dirname(__DIR__, 2); // /path/to/project
    }
    
    /** @test */
    public function publicDirectoryExists(): void
    {
        $publicDir = $this->projectRoot . '/public';
        $this->assertDirectoryExists($publicDir);
    }
    
    /** @test */
    public function publicContainsFrontController(): void
    {
        $indexFile = $this->projectRoot . '/public/index.php';
        $this->assertFileExists($indexFile);
    }
    
    /** @test */
    public function publicContainsAssetsDirectory(): void
    {
        $assetsDir = $this->projectRoot . '/public/assets';
        $this->assertDirectoryExists($assetsDir);
    }
    
    /** @test */
    public function srcDirectoryIsOutsidePublic(): void
    {
        $srcDir = $this->projectRoot . '/src';
        $publicDir = $this->projectRoot . '/public';
        
        // src/는 public/ 부모이거나 형제여야 함
        $this->assertNotStringStartsWith(
            $publicDir,
            $srcDir,
            'src/ must not be inside public/'
        );
    }
    
    /** @test */
    public function configDirectoryIsOutsidePublic(): void
    {
        $configDir = $this->projectRoot . '/config';
        $publicDir = $this->projectRoot . '/public';
        
        $this->assertNotStringStartsWith(
            $publicDir,
            $configDir,
            'config/ must not be inside public/'
        );
    }
    
    /** @test */
    public function vendorDirectoryIsOutsidePublic(): void
    {
        $vendorDir = $this->projectRoot . '/vendor';
        $publicDir = $this->projectRoot . '/public';
        
        $this->assertNotStringStartsWith(
            $publicDir,
            $vendorDir,
            'vendor/ must not be inside public/'
        );
    }
    
    /** @test */
    public function sensitiveFilesNotInPublic(): void
    {
        $publicDir = $this->projectRoot . '/public';
        
        $sensitiveFiles = [
            'composer.json',
            'composer.lock',
            '.env',
            'config.php',
        ];
        
        foreach ($sensitiveFiles as $file) {
            $path = $publicDir . '/' . $file;
            $this->assertFileDoesNotExist(
                $path,
                "Sensitive file '$file' must not be in public/"
            );
        }
    }
}
```

### 7.2 웹 접근 불가 테스트 (integration test)

웹 서버를 통해 document root 외부 파일에 접근할 수 없는지 확인한다.

```php
// php/tests/Integration/PublicDocrootAccessTest.php
namespace MintWiki\Tests\Integration;

use PHPUnit\Framework\TestCase;

final class PublicDocrootAccessTest extends TestCase
{
    private string $baseUrl = 'http://localhost:8000';
    
    /** @test */
    public function cannotAccessSrcDirectory(): void
    {
        $response = $this->getHttp('/src/App/Application.php');
        $this->assertEquals(404, $response['status']);
    }
    
    /** @test */
    public function cannotAccessConfigDirectory(): void
    {
        $response = $this->getHttp('/config/config.php');
        $this->assertEquals(404, $response['status']);
    }
    
    /** @test */
    public function cannotAccessVendorDirectory(): void
    {
        $response = $this->getHttp('/vendor/autoload.php');
        $this->assertEquals(404, $response['status']);
    }
    
    /** @test */
    public function cannotAccessComposerJson(): void
    {
        $response = $this->getHttp('/composer.json');
        $this->assertEquals(404, $response['status']);
    }
    
    /** @test */
    public function canAccessPublicAssets(): void
    {
        // assets/ 디렉토리가 있다면 접근 가능해야 함
        $response = $this->getHttp('/assets/');
        // 200 또는 403 (directory listing 차단) — 404 아님
        $this->assertNotEquals(404, $response['status']);
    }
    
    /** @test */
    public function canAccessFrontController(): void
    {
        $response = $this->getHttp('/');
        $this->assertEquals(200, $response['status']);
    }
    
    private function getHttp(string $path): array
    {
        $url = $this->baseUrl . $path;
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        
        curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        return ['status' => (int)$status];
    }
}
```

### 7.3 배포 체크리스트

배포 전 수동 검증:

```bash
#!/bin/bash
# scripts/verify-docroot.sh

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC_DIR="$PROJECT_ROOT/public"

# 1. public/ 존재
if [ ! -d "$PUBLIC_DIR" ]; then
    echo "❌ public/ directory not found"
    exit 1
fi
echo "✓ public/ directory exists"

# 2. public/index.php 존재
if [ ! -f "$PUBLIC_DIR/index.php" ]; then
    echo "❌ public/index.php not found"
    exit 1
fi
echo "✓ public/index.php exists"

# 3. src/ document root 외부
if [[ "$PUBLIC_DIR" == *"/src/"* ]]; then
    echo "❌ src/ is inside public/"
    exit 1
fi
echo "✓ src/ is outside public/"

# 4. 민감한 파일들 document root 외부
for file in config composer.json .env .env.local; do
    if [ -f "$PUBLIC_DIR/$file" ]; then
        echo "❌ Sensitive file '$file' is in public/"
        exit 1
    fi
done
echo "✓ Sensitive files are outside public/"

echo ""
echo "✅ All docroot checks passed"
exit 0
```

실행:

```bash
bash scripts/verify-docroot.sh
```

## 8. 호스팅사별 설정 가이드

### 8.1 cPanel

1. **주 도메인 또는 Addon Domain 추가**
2. 제어판 → **Domains** 섹션
3. 도메인 설정 → **Document Root**
4. 기본값: `/public_html` → **변경**: `/public_html/public`
5. **저장**

### 8.2 Plesk

1. **Domains** 메뉴
2. 도메인 선택 → **Hosting & Performance** → **Web Hosting**
3. **Document Root**: `/domains/example.com/public` (기본값: `/public_html`)
4. 저장

### 8.3 DirectAdmin

1. **Account Manager** → **Domain Management**
2. 도메인 선택 → **Public HTML** 경로
3. 기본값: `/public_html` → **변경**: `/public_html/public`

### 8.4 자체 VPS/Dedicated 서버

호스팅사가 document root 변경을 허용하지 않으면, 다음 방법 중 선택:

**옵션 A: 호스팅사 기술 지원 요청**
- "Document root를 `/public_html/public`으로 변경해 달라"고 요청
- 대부분 수용

**옵션 B: Symbolic Link (심볼릭 링크)**

```bash
# /home/user/public_html에서
rm -rf /home/user/public_html/*
ln -s /home/user/app/public /home/user/public_html/public
cp /home/user/app/public/index.php /home/user/public_html/index.php
```

단점: 복잡하고 유지보수 어려움

**옵션 C: 배포 구조 변경**

프로젝트 루트를 `/home/user/public_html`로 설정하되, 웹 접근을 `public/`로 제한:

```apache
# /public_html/.htaccess
RewriteEngine On
RewriteBase /
RewriteCond %{REQUEST_URI} !^/public/
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /public/$1 [L]
```

권장하지 않음: 성능 저하, 보안 위험.

## 9. 보안 고려사항

### 9.1 웹 서버 오류 설정

설정 오류 시에도 source code가 노출되지 않도록:

```php
// public/index.php 시작 부분
error_reporting(E_ALL);
ini_set('display_errors', '0');  // 브라우저에 오류 노출 안 함
ini_set('log_errors', '1');
ini_set('error_log', __DIR__ . '/../storage/logs/php_errors.log');

// 또는
set_error_handler(function($errno, $errstr, $errfile, $errline) {
    // 프로젝트 루트 외부 경로는 로그에만 기록, 브라우저에는 노출 안 함
    $safe_errfile = str_replace(
        dirname(__DIR__),
        '/<project>',
        $errfile
    );
    error_log("[$errno] $errstr in $safe_errfile:$errline");
    return true;
});
```

### 9.2 Directory Listing 차단

웹 서버가 디렉토리 목록을 표시하지 않도록:

**Apache (.htaccess in public/)**:

```apache
Options -Indexes
```

**Nginx**:

```nginx
autoindex off;
```

### 9.3 파일 접근 권한 (chmod)

```bash
# 호스팅 계정에서
find /home/user/public_html -type f -exec chmod 644 {} \;  # 파일
find /home/user/public_html -type d -exec chmod 755 {} \;  # 디렉토리

# 더 엄격하게
chmod 600 /home/user/public_html/config/config.php        # config 읽기만
chmod 600 /home/user/public_html/config/local-config.php
chmod 600 /home/user/public_html/composer.json
chmod 600 /home/user/public_html/composer.lock
chmod 600 /home/user/public_html/.env
```

### 9.4 `.htaccess` 재정의 방지 (Apache)

root 디렉토리의 `.htaccess`가 public/ 내 설정을 재정의하지 않도록:

```apache
# /public_html/.htaccess
# 또는 없음 (public/ 외부는 front controller로 라우팅하지 않음)

# /public_html/public/.htaccess에만 규칙 정의
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^ index.php [L]
</IfModule>
```

## 10. 트레이드오프와 제약

### 10.1 배포 구조 변경 필요

표준 프로젝트 구조를 호스팅에 맞게 조정해야 한다.

**장점**:
- 웹 서버만으로 document root 제한 가능 (추가 설정 불필요)
- 실수로 인한 파일 노출 방지

**단점**:
- 배포 스크립트에서 `public/`만 업로드해야 함
- 개발 환경과 배포 환경의 구조가 다를 수 있음

### 10.2 document root 변경 불가 호스팅

일부 저가 호스팅은 document root 변경을 허용하지 않는다.

**해결 방법**:
- 호스팅사 기술 지원 요청 (대부분 수용)
- 다른 호스팅사 선택
- Rewrite 규칙으로 우회 (권장하지 않음)

### 10.3 URL 경로 구조

`public/`으로 document root를 설정하면:

```
# 빌드 가능한 시나리오
GET /documents                      → public/index.php → 라우팅
GET /assets/css/app.css             → public/assets/css/app.css (정적)

# 불가능한 시나리오 (document root 외부)
GET /src/Http/Router.php            → 404 (의도된 동작)
```

이는 의도된 설계이며, 제약이 아니라 **보안 기능**이다.

## 관련 문서

- [Shared Hosting Target Baseline](shared-hosting-target-baseline.md) — 호스팅 환경 요구사항
- [PHP Runtime Bootstrap](php-runtime-bootstrap.md) — Front controller와 설정 로드
- [PHP Static Asset Serving](php-static-asset-serving.md) — `assets/` 디렉토리 정책
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md) — HTTP 캐싱
- [PHP Runtime Security Baseline](php-runtime-security-baseline.md) — 보안 기초

## 후속 태스크 연결

- **0613**: `.htaccess` front controller 규칙 (Apache 호스팅에서 라우팅 구현)
- **0627**: Config file loader (document root 외부 `config/` 로드)
- **0628-0630**: Storage directory checks (document root 외부 `storage/` 접근)
- **배포 태스크**: `public/` 디렉토리만 업로드하는 배포 스크립트
