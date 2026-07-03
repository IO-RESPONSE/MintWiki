# PHP UI Robots Policy

**Phase D: Server-rendered UI after PHP and DB (0521-0610)** 문서.
서버 렌더링 UI에서 검색 엔진 봇(robots)이 접근할 수 있는 경로와 차단해야 하는 경로를 정의한다.
비공개 페이지(관리자, API, 설치 페이지)는 `robots.txt`와 메타 태그로 차단한다.

## 목적

MintWiki는 공개 위키이므로 문서 콘텐츠는 검색 엔진에 색인되어야 한다.
하지만 다음 페이지들은 색인되면 안 된다:

- **관리자 페이지** (`/admin/*`): 시스템 상태, 감사 로그, 사용자 차단 등 민감한 정보
- **API 엔드포인트** (`/api/*`): 기계 가독 포맷, SEO에 불필요
- **설치 페이지** (`/installer/*`): 설치 과정 중 임시 페이지, 일반 사용자에게 노출 불필요
- **인증 페이지** (`/login`, `/logout`): 사용자 인증 과정 중간 페이지

이 문서는 다음을 정의한다:

- **robots.txt 구성**: 봇 접근 차단 규칙
- **메타 태그 정책**: HTML 응답에서 `<meta name="robots">`로 추가 제어
- **User-Agent별 규칙**: 특정 봇(예: GPT-4 web crawler) 차단 규칙
- **공개 경로 선언**: 검색 엔진이 우선적으로 색인할 경로

## robots.txt 구성

### 파일 위치

`robots.txt`는 웹사이트 루트(`/`)에 배치된다.

```
/robots.txt
```

PHP 애플리케이션에서는 GET `/robots.txt` 요청을 정적 파일 또는 동적 핸들러로 서빙한다.

### 기본 규칙

```
User-Agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /installer/
Disallow: /login
Disallow: /logout
Disallow: /*?*sort=
Disallow: /*?*page=
Allow: /documents/
Allow: /search
Allow: /
```

### 규칙 설명

#### 1. 전역 차단 (모든 User-Agent)

```
User-Agent: *
```

특정 봇을 언급하지 않으면 모든 봇에 적용된다.

#### 2. 관리자 경로 차단

```
Disallow: /admin/
```

다음 경로들을 차단한다:

- `/admin` — 관리자 대시보드 (authentication required)
- `/admin/status` — 시스템 상태 페이지
- `/admin/reporting` — 신고 관리 페이지
- `/admin/audit` — 감사 로그 조회 페이지
- `/admin/block-user` — 사용자 차단 기능

#### 3. API 엔드포인트 차단

```
Disallow: /api/
```

다음 경로들을 차단한다:

- `/api/documents` — 문서 목록 (JSON 형식)
- `/api/documents/by-title` — 제목 검색 API

**이유**: API는 기계 가독 형식이므로 SEO가 불필요하고, 잦은 요청은 서버 부하 증가.

#### 4. 설치 페이지 차단

```
Disallow: /installer/
```

다음 경로들을 차단한다:

- `/installer/diagnose` — 데이터베이스 연결 진단
- `/installer/status` — 스키마 마이그레이션 상태

**이유**: 설치 완료 후에만 필요하며, 일반 사용자는 접근 불가.
검색 엔진이 색인하면 설치되지 않은 인스턴스로 착각할 수 있음.

#### 5. 인증 페이지 차단

```
Disallow: /login
Disallow: /logout
```

**이유**: 인증 페이지는 개별 사용자 세션에 필요하며 공개 콘텐츠가 아님.

#### 6. 쿼리 매개변수 차단

```
Disallow: /*?*sort=
Disallow: /*?*page=
```

**이유**: 정렬과 페이지 매개변수로 인한 중복 색인 방지.

- `/documents?page=1`, `/documents?page=2` → 동일 콘텐츠, 다른 URL
- `/documents?sort=title`, `/documents?sort=date` → 동일 콘텐츠, 다른 URL

#### 7. 공개 경로 명시

```
Allow: /documents/
Allow: /search
Allow: /
```

모든 공개 경로는 명시적으로 `Allow:`한다. 이는 관리자 경로의 `Disallow:`가 더 구체적일 때 명확성을 높인다.

### 확장된 robots.txt 예시

특정 봇을 차단해야 하는 경우:

```
# OpenAI GPT-4 Web Crawler
User-Agent: GPTBot
Disallow: /

# Anthropic Claude Web Crawler
User-Agent: Claude-Web
Disallow: /

# CCBot (Common Crawl)
User-Agent: CCBot
Disallow: /
```

이러한 규칙은 각 조직의 정책에 따라 추가된다.

## 메타 태그 정책

`robots.txt`는 검색 엔진에 대한 **요청(request)**이지, 강제 규칙이 아니다.
보다 강력한 제어를 위해 HTML 응답 헤더와 메타 태그를 사용한다.

### 메타 태그 위치

`<head>` 섹션에 다음 형식으로 추가한다:

```html
<meta name="robots" content="noindex, nofollow">
```

### 메타 태그 값

| 값 | 의미 | 사용 경우 |
|---|---|---|
| `index` | 이 페이지를 색인하도록 허용 | (기본값) 공개 페이지 |
| `noindex` | 이 페이지를 색인하지 말 것 | 관리자, API, 설치 페이지 |
| `follow` | 페이지 내 링크를 따라가도록 허용 | (기본값) 공개 페이지 |
| `nofollow` | 페이지 내 링크를 따라가지 말 것 | 관리자, API 페이지 |

### 페이지별 정책

#### 공개 문서 페이지 (`/documents/*`)

```html
<!-- 색인 O, 링크 따라가기 O (기본값) -->
<meta name="robots" content="index, follow">
```

또는 명시적으로 생략 (기본값과 동일):

```html
<!-- 생략 가능 -->
```

#### 검색 페이지 (`/search`)

```html
<meta name="robots" content="noindex, follow">
```

**이유**: 검색 결과 페이지는 중복 색인을 유발하므로 색인하지 않음.
하지만 검색 페이지 내 문서 링크는 따라가기 허용.

#### 관리자 페이지 (`/admin/*`)

```html
<meta name="robots" content="noindex, nofollow">
```

**이유**: 관리자 페이지는 완전히 숨긴다.

#### API 엔드포인트 (`/api/*`)

API는 HTML이 아니므로 메타 태그를 포함할 수 없다.
대신 HTTP 헤더로 제어한다:

```php
// API 응답 헤더
header('X-Robots-Tag: noindex, nofollow');
```

#### 설치 페이지 (`/installer/*`)

```html
<meta name="robots" content="noindex, nofollow">
```

#### 인증 페이지 (`/login`, `/logout`)

```html
<meta name="robots" content="noindex, nofollow">
```

### 구현 위치

#### 레이아웃 (Layout.php)

대부분의 페이지는 `Layout.php`를 통해 `<head>`를 생성한다.
레이아웃은 현재 요청의 경로를 확인하여 적절한 메타 태그를 출력한다:

```php
// php/src/Ui/Layout.php
public function render(string $bodyHtml): string
{
    $robotsMeta = $this->getRobotsMetaTag();
    
    return <<<HTML
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{$this->title}</title>
        {$robotsMeta}
    </head>
    <body>
        {$bodyHtml}
    </body>
    </html>
    HTML;
}

private function getRobotsMetaTag(): string
{
    // 관리자 경로
    if (str_starts_with($this->currentPath, '/admin')) {
        return '<meta name="robots" content="noindex, nofollow">';
    }
    
    // 설치 경로
    if (str_starts_with($this->currentPath, '/installer')) {
        return '<meta name="robots" content="noindex, nofollow">';
    }
    
    // 인증 경로
    if (in_array($this->currentPath, ['/login', '/logout'])) {
        return '<meta name="robots" content="noindex, nofollow">';
    }
    
    // 검색 결과 (중복 색인 방지)
    if ($this->currentPath === '/search') {
        return '<meta name="robots" content="noindex, follow">';
    }
    
    // 기본값: 공개 페이지는 색인 허용
    return '<meta name="robots" content="index, follow">';
}
```

#### API 응답

API 엔드포인트는 HTML이 아니므로, HTTP 헤더로 robots 정책을 전달한다:

```php
// php/src/Http/ApiDocumentListHandler.php
public function handle(): Response
{
    // ... API 로직 ...
    
    return Response::json(
        ['documents' => $documents],
        headers: [
            'X-Robots-Tag' => 'noindex, nofollow'
        ]
    );
}
```

## robots.txt 동적 생성 vs 정적 파일

### 옵션 1: 정적 파일 (권장)

`public/robots.txt`에 고정된 파일을 배치한다.

```
# public/robots.txt
User-Agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /installer/
Disallow: /login
Disallow: /logout
Disallow: /*?*sort=
Disallow: /*?*page=
Allow: /documents/
Allow: /search
Allow: /
```

**장점**:
- 웹서버(Apache/Nginx)가 직접 서빙, PHP 실행 불필요
- 빠른 응답
- 캐싱 용이

**단점**:
- 경로 변경 시 수동 업데이트

### 옵션 2: 동적 생성 (유연함)

PHP 핸들러에서 요청할 때마다 생성한다:

```php
// php/src/Http/RobotsTxtHandler.php
final class RobotsTxtHandler
{
    public function handle(Request $request): Response
    {
        $content = <<<TXT
        User-Agent: *
        Disallow: /admin/
        Disallow: /api/
        Disallow: /installer/
        Disallow: /login
        Disallow: /logout
        Disallow: /*?*sort=
        Disallow: /*?*page=
        Allow: /documents/
        Allow: /search
        Allow: /
        TXT;
        
        return Response::text($content, headers: [
            'Cache-Control' => 'max-age=86400, public',
        ]);
    }
}
```

라우터에 등록:

```php
// php/src/Routes.php
$router->register('GET', '/robots.txt', RobotsTxtHandler::class);
```

**장점**:
- 경로 변경 시 PHP 코드만 수정
- 환경(개발/프로덕션)에 따라 다른 규칙 적용 가능

**단점**:
- PHP 실행 오버헤드
- 조건부 로직이 복잡해질 수 있음

## sitemap.xml 정책

`robots.txt`와 함께, `sitemap.xml`을 제공하면 검색 엔진이 더 효율적으로 색인한다.

### 구조

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/documents</loc>
    <lastmod>2025-07-03T12:00:00Z</lastmod>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://example.com/documents/abc123</loc>
    <lastmod>2025-07-03T10:30:00Z</lastmod>
    <priority>0.8</priority>
  </url>
  <!-- 더 많은 문서 URL들 -->
</urlset>
```

### 포함 대상

- 모든 공개 문서 (`/documents/*`)
- 메인 페이지 (`/`)
- 검색 페이지 (`/search`)

### 제외 대상

- `/admin/*` — 관리자 페이지
- `/api/*` — API 엔드포인트
- `/installer/*` — 설치 페이지
- `/login`, `/logout` — 인증 페이지

### 구현 (미래 태스크)

```php
// php/src/Http/SitemapHandler.php
final class SitemapHandler
{
    public function __construct(
        private DocumentRepository $documents,
    ) {}

    public function handle(): Response
    {
        $urls = [
            ['loc' => 'https://example.com/', 'priority' => '1.0'],
            ['loc' => 'https://example.com/search', 'priority' => '0.9'],
        ];
        
        foreach ($this->documents->all() as $doc) {
            $urls[] = [
                'loc' => "https://example.com/documents/{$doc->id()}",
                'lastmod' => $doc->updatedAt()->format('c'),
                'priority' => '0.8',
            ];
        }
        
        // XML 생성 로직
        return Response::xml($this->buildSitemap($urls));
    }
}
```

`robots.txt`에 sitemap 참조 추가:

```
Sitemap: https://example.com/sitemap.xml
```

## 테스트 전략

### 1. robots.txt 형식 검증 (수동)

```bash
# robots.txt 다운로드 및 확인
curl -s https://example.com/robots.txt | head -20

# 예상 출력
User-Agent: *
Disallow: /admin/
Disallow: /api/
...
```

### 2. robots.txt 컨텐츠 테스트

```php
// tests/Http/RobotsTxtHandlerTest.php
final class RobotsTxtHandlerTest
{
    public function test_robots_txt_blocks_admin_paths(): void
    {
        $handler = new RobotsTxtHandler();
        $response = $handler->handle(new Request('GET', '/robots.txt'));
        
        $this->assertStringContainsString('Disallow: /admin/', $response->body());
    }

    public function test_robots_txt_blocks_api_paths(): void
    {
        $handler = new RobotsTxtHandler();
        $response = $handler->handle(new Request('GET', '/robots.txt'));
        
        $this->assertStringContainsString('Disallow: /api/', $response->body());
    }

    public function test_robots_txt_blocks_installer_paths(): void
    {
        $handler = new RobotsTxtHandler();
        $response = $handler->handle(new Request('GET', '/robots.txt'));
        
        $this->assertStringContainsString('Disallow: /installer/', $response->body());
    }

    public function test_robots_txt_allows_documents(): void
    {
        $handler = new RobotsTxtHandler();
        $response = $handler->handle(new Request('GET', '/robots.txt'));
        
        $this->assertStringContainsString('Allow: /documents/', $response->body());
    }
}
```

### 3. 메타 태그 검증

```php
// tests/Ui/RobotsMetaTagTest.php
final class RobotsMetaTagTest
{
    public function test_admin_page_has_noindex_meta_tag(): void
    {
        $layout = new Layout(currentPath: '/admin/status', title: 'Admin');
        $html = $layout->render('<p>Status</p>');
        
        $this->assertStringContainsString(
            '<meta name="robots" content="noindex, nofollow">',
            $html
        );
    }

    public function test_public_document_page_has_index_meta_tag(): void
    {
        $layout = new Layout(currentPath: '/documents/abc123', title: 'Document');
        $html = $layout->render('<p>Content</p>');
        
        $this->assertStringContainsString(
            '<meta name="robots" content="index, follow">',
            $html
        );
    }

    public function test_search_page_has_noindex_follow_meta_tag(): void
    {
        $layout = new Layout(currentPath: '/search', title: 'Search');
        $html = $layout->render('<p>Results</p>');
        
        $this->assertStringContainsString(
            '<meta name="robots" content="noindex, follow">',
            $html
        );
    }

    public function test_installer_page_has_noindex_meta_tag(): void
    {
        $layout = new Layout(currentPath: '/installer/status', title: 'Installer');
        $html = $layout->render('<p>Status</p>');
        
        $this->assertStringContainsString(
            '<meta name="robots" content="noindex, nofollow">',
            $html
        );
    }

    public function test_login_page_has_noindex_meta_tag(): void
    {
        $layout = new Layout(currentPath: '/login', title: 'Login');
        $html = $layout->render('<p>Login form</p>');
        
        $this->assertStringContainsString(
            '<meta name="robots" content="noindex, nofollow">',
            $html
        );
    }
}
```

### 4. SEO 크롤러 시뮬레이션 (통합 테스트)

```php
// tests/Integration/RobotsCrawlerSimulationTest.php
final class RobotsCrawlerSimulationTest
{
    public function test_google_crawler_cannot_index_admin(): void
    {
        // robots.txt 파싱
        $robotsContent = $this->getRobotsContent();
        $parser = new RobotsParser($robotsContent);
        
        // Google crawler를 기준으로 테스트
        $isAllowed = $parser->isAllowed('/admin/status', 'Googlebot');
        $this->assertFalse($isAllowed);
    }

    public function test_google_crawler_can_index_documents(): void
    {
        $robotsContent = $this->getRobotsContent();
        $parser = new RobotsParser($robotsContent);
        
        $isAllowed = $parser->isAllowed('/documents/abc123', 'Googlebot');
        $this->assertTrue($isAllowed);
    }
}
```

## 주의사항

### 1. robots.txt는 권장(advisory)이지, 강제가 아님

악의적인 봇은 robots.txt를 무시할 수 있다.
강력한 보안이 필요한 경우:

```php
// IP 기반 차단 (더 강력)
if (!$this->isAllowedIp($_SERVER['REMOTE_ADDR'])) {
    return Response::status(403, 'Forbidden');
}

// 인증 요구
if (str_starts_with($this->currentPath, '/admin') && !$this->isAuthenticated()) {
    return Response::status(401, 'Unauthorized');
}
```

### 2. 메타 태그와 HTTP 헤더의 우선순위

HTTP `X-Robots-Tag` 헤더가 HTML 메타 태그보다 우선한다:

```php
// 예: API는 헤더로 제어
header('X-Robots-Tag: noindex');

// 메타 태그와 충돌 시 헤더가 승리
```

### 3. 검색 엔진별 해석 차이

- **Google**: `index`, `noindex`, `follow`, `nofollow` 완벽 지원
- **Bing**: 대부분 지원하지만 일부 메타 값 무시
- **기타**: 구현에 따라 다름

표준 규칙만 사용하는 것이 안전하다.

### 4. 성능: robots.txt 캐싱

정적 파일로 제공하거나, 캐시 헤더를 설정한다:

```php
header('Cache-Control: max-age=86400, public');  // 1일
```

이렇게 하면 검색 엔진 크롤러가 자주 요청하지 않는다.

## 관련 문서

- [PHP UI SEO Basics](php-ui-seo-basics.md) — meta/title/canonical 정책
- [PHP UI Installer Link Policy](php-ui-installer-link-policy.md) — 설치 경로 및 링크
- [PHP UI Cache Header Policy](php-ui-cache-header-policy.md) — 캐시 헤더 정책
- [Shared Hosting Migration Policy](shared-hosting-migration-policy.md) — 호스팅 환경 구성

## 이 문서 이후 단계

- **0595** (이 태스크): Robots 정책 문서화. 실제 구현은 아직 미루어짐.
- **0595 이후** (미래 태스크): `public/robots.txt` 정적 파일 또는 `RobotsTxtHandler` 구현
- **0595 이후** (미래 태스크): `Layout.php`에서 robots 메타 태그 구현
- **0595 이후** (미래 태스크): API 응답에 `X-Robots-Tag` 헤더 추가
- **0595 이후** (미래 태스크): `SitemapHandler` 구현 및 `/sitemap.xml` 제공
