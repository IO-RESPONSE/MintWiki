<?php

declare(strict_types=1);

/**
 * `public/index.php`가 등록하는 GET / (대문/프론트페이지) route 핸들러의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다
 * (0419 HealthRouteTest.php와 동일한 방식).
 *
 * 0693에서 홈이 인라인 검색 폼 HTML 문자열 대신 `FrontPage` 컴포넌트로
 * 개편되었다 — 검색 영역 + 최근 편집된 문서 목록(있으면) + 사이트 소개
 * 안내를 0691 스킨(상단바/푸터) 위에 렌더링한다. index.php는 재사용
 * 가능한 모듈이 아니므로, 동일한 등록 로직을 Router에 그대로 재구성해
 * 검증한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Ui\FrontPage;
use MintWiki\Ui\Layout;
use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationBar;

$failures = [];

/**
 * `public/index.php`의 GET / 핸들러와 동일하게(태스크 0691, 0693), 상단
 * 네비게이션 바를 header에 주입한 Layout으로 FrontPage를 렌더링하는
 * route를 등록한다.
 *
 * @param Document[] $recentDocuments
 */
function makeHomeRouter(array $recentDocuments): Router
{
    $router = new Router();

    $headerContent = (new NavigationBar())->render(new Navigation(), '/', []);
    $layout = new Layout(null, $headerContent);

    $router->register('GET', '/', static function () use ($layout, $recentDocuments): Response {
        $frontPage = new FrontPage(null, $layout);

        return Response::html($frontPage->render($recentDocuments));
    });

    return $router;
}

$expectedHtmlHeaders = [
    'Content-Type' => 'text/html; charset=utf-8',
    'Cache-Control' => 'no-cache, no-store, must-revalidate',
    'X-Content-Type-Options' => 'nosniff',
    'X-Frame-Options' => 'DENY',
    'Content-Security-Policy' => "default-src 'self'",
];

// ============================================================================
// 1. 최근 문서가 없는 경우 (DB 미설정/빈 상태)
// ============================================================================

$router = makeHomeRouter([]);
$handler = $router->match(new Request('GET', '/'));

if ($handler === null) {
    $failures[] = 'GET / route는 등록되어 있어야 한다.';
} else {
    $response = $handler();

    // (1-1) 기본 요청에 대해 200 상태코드와 HTML Content-Type을 반환해야 한다.
    if ($response->status() !== 200) {
        $failures[] = 'GET / 응답의 status는 200이어야 한다.';
    }
    if ($response->headers() !== $expectedHtmlHeaders) {
        $failures[] = 'GET / 응답의 Content-Type은 text/html; charset=utf-8이어야 한다.';
    }

    $body = $response->body();

    // (1-2) HTML 응답이 기본 Layout(0691 스킨)으로 감싸져 있어야 한다.
    if (!str_contains($body, '<!doctype html>')) {
        $failures[] = 'HTML 응답이 doctype을 포함해야 한다.';
    }
    if (!str_contains($body, '<html lang="ko">')) {
        $failures[] = 'HTML 응답이 기본 언어를 ko로 설정해야 한다.';
    }
    if (!str_contains($body, '<title>MintWiki</title>')) {
        $failures[] = 'HTML 응답의 title이 MintWiki여야 한다.';
    }
    if (!str_contains($body, '<header><nav class="site-nav"')) {
        $failures[] = 'HTML 응답의 header가 상단 네비게이션 바(0690)를 포함해야 한다.';
    }
    if (!str_contains($body, '<a class="site-nav__brand" href="/">MintWiki</a>')) {
        $failures[] = 'HTML 응답의 상단 네비게이션 바가 브랜드 로고를 포함해야 한다.';
    }
    if (!str_contains($body, '<footer>')) {
        $failures[] = 'HTML 응답이 footer landmark를 포함해야 한다.';
    }
    if (!str_contains($body, '<div class="site-footer-info">')) {
        $failures[] = 'HTML 응답의 footer가 나무위키풍 사이트 정보를 포함해야 한다.';
    }

    // (1-3) 눈에 띄는 검색 영역을 포함해야 한다.
    if (!str_contains($body, 'class="front-page__search"')) {
        $failures[] = 'HTML 응답이 대문 검색 영역을 포함해야 한다.';
    }
    if (!str_contains($body, '<form method="get" action="/api/documents/by-title"')) {
        $failures[] = 'HTML 응답이 문서 검색 form을 포함해야 한다.';
    }
    if (!str_contains($body, '<input type="text" name="q"')) {
        $failures[] = 'HTML 응답이 검색어 입력 필드를 포함해야 한다.';
    }
    if (!str_contains($body, '검색</button>')) {
        $failures[] = 'HTML 응답이 검색 버튼을 포함해야 한다.';
    }

    // (1-4) 사이트 소개/안내 블록을 포함해야 한다.
    if (!str_contains($body, 'class="front-page__about"')) {
        $failures[] = 'HTML 응답이 사이트 소개 블록을 포함해야 한다.';
    }

    // (1-5) 최근 문서가 없으면 빈 상태 안내를 보여줘야 한다.
    if (!str_contains($body, 'class="front-page__recent"')) {
        $failures[] = 'HTML 응답이 최근 편집된 문서 영역을 포함해야 한다.';
    }
    if (!str_contains($body, 'class="empty-state"')) {
        $failures[] = '최근 문서가 없으면 빈 상태 안내(EmptyState)를 보여줘야 한다.';
    }
    if (str_contains($body, 'front-page__recent-list')) {
        $failures[] = '최근 문서가 없으면 목록(front-page__recent-list)을 렌더링하지 않아야 한다.';
    }
}

// ============================================================================
// 2. 최근 문서가 있는 경우
// ============================================================================

$recentDocuments = [
    new Document('doc-1', '최근 문서 A'),
    new Document('doc-2', '최근 문서 B'),
];
$router = makeHomeRouter($recentDocuments);
$handler = $router->match(new Request('GET', '/'));

if ($handler === null) {
    $failures[] = '(최근 문서 있음) GET / route는 등록되어 있어야 한다.';
} else {
    $body = $handler()->body();

    if (!str_contains($body, 'class="front-page__recent-list"')) {
        $failures[] = '최근 문서가 있으면 목록을 렌더링해야 한다.';
    }
    if (str_contains($body, 'class="empty-state"')) {
        $failures[] = '최근 문서가 있으면 빈 상태 안내를 보여주지 않아야 한다.';
    }
    if (!str_contains($body, '<a href="/wiki/' . rawurlencode('최근 문서 A') . '">최근 문서 A</a>')) {
        $failures[] = '최근 문서 목록이 문서 제목과 /wiki/{title} 링크를 포함해야 한다.';
    }
    if (!str_contains($body, '<a href="/wiki/' . rawurlencode('최근 문서 B') . '">최근 문서 B</a>')) {
        $failures[] = '최근 문서 목록이 두 번째 문서도 포함해야 한다.';
    }
}

// ============================================================================
// 3. 등록되지 않은 다른 method/path는 여전히 매칭되지 않아야 한다.
// ============================================================================

$router = makeHomeRouter([]);
if ($router->match(new Request('POST', '/')) !== null) {
    $failures[] = 'POST /는 등록되어 있지 않으므로 null을 반환해야 한다.';
}
if ($router->match(new Request('GET', '/health')) !== null) {
    $failures[] = 'GET /health는 등록되어 있지 않으므로 null을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "GET / (대문/프론트페이지) route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET / (대문/프론트페이지) route 테스트 통과.\n");
exit(0);
