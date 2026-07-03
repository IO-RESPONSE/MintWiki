<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0526에서 등록하는 GET / (home page) route 핸들러의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다
 * (0419 HealthRouteTest.php와 동일한 방식).
 *
 * 홈페이지는 문서 검색 진입점을 제공한다. HTML 응답을 반환하고, Layout을
 * 이용해 기본 문서 구조를 갖춘다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Ui\Layout;

$failures = [];

$router = new Router();
$layout = new Layout();

$expectedHtmlHeaders = [
    'Content-Type' => 'text/html; charset=utf-8',
    'Cache-Control' => 'no-cache, no-store, must-revalidate',
    'X-Content-Type-Options' => 'nosniff',
    'X-Frame-Options' => 'DENY',
    'Content-Security-Policy' => "default-src 'self'",
];

$router->register('GET', '/', static function () use ($layout): Response {
    $body = '<main>'
        . '<h1>문서 검색</h1>'
        . '<form method="get" action="/api/documents/by-title">'
        . '<input type="text" name="q" placeholder="검색어를 입력하세요" required>'
        . '<button type="submit">검색</button>'
        . '</form>'
        . '</main>';

    return Response::html($layout->render('MintWiki', $body));
});

// (1) 기본 요청에 대해 200 상태코드와 HTML Content-Type을 반환해야 한다.
$handler = $router->match(new Request('GET', '/'));
if ($handler === null) {
    $failures[] = 'GET / route는 등록되어 있어야 한다.';
} else {
    $response = $handler();
    if ($response->status() !== 200) {
        $failures[] = 'GET / 응답의 status는 200이어야 한다.';
    }
    if ($response->headers() !== $expectedHtmlHeaders) {
        $failures[] = 'GET / 응답의 Content-Type은 text/html; charset=utf-8이어야 한다.';
    }
}

// (2) HTML 응답이 기본 Layout으로 감싸져 있어야 한다.
if ($handler !== null) {
    $response = $handler();
    $body = $response->body();

    if (!str_contains($body, '<!doctype html>')) {
        $failures[] = 'HTML 응답이 doctype을 포함해야 한다.';
    }
    if (!str_contains($body, '<html lang="ko">')) {
        $failures[] = 'HTML 응답이 기본 언어를 ko로 설정해야 한다.';
    }
    if (!str_contains($body, '<title>MintWiki</title>')) {
        $failures[] = 'HTML 응답의 title이 MintWiki여야 한다.';
    }
    if (!str_contains($body, '<header></header>')) {
        $failures[] = 'HTML 응답이 header landmark를 포함해야 한다.';
    }
    if (!str_contains($body, '<footer></footer>')) {
        $failures[] = 'HTML 응답이 footer landmark를 포함해야 한다.';
    }
}

// (3) 문서 검색 진입점을 포함해야 한다.
if ($handler !== null) {
    $response = $handler();
    $body = $response->body();

    if (!str_contains($body, '<h1>문서 검색</h1>')) {
        $failures[] = 'HTML 응답이 "문서 검색" 제목을 포함해야 한다.';
    }
    if (!str_contains($body, '<form method="get" action="/api/documents/by-title">')) {
        $failures[] = 'HTML 응답이 문서 검색 form을 포함해야 한다.';
    }
    if (!str_contains($body, '<input type="text" name="q"')) {
        $failures[] = 'HTML 응답이 검색어 입력 필드를 포함해야 한다.';
    }
    if (!str_contains($body, '<button type="submit">검색</button>')) {
        $failures[] = 'HTML 응답이 검색 버튼을 포함해야 한다.';
    }
}

// (4) 등록되지 않은 다른 method/path는 여전히 매칭되지 않아야 한다.
if ($router->match(new Request('POST', '/')) !== null) {
    $failures[] = 'POST /는 등록되어 있지 않으므로 null을 반환해야 한다.';
}
if ($router->match(new Request('GET', '/health')) !== null) {
    $failures[] = 'GET /health는 등록되어 있지 않으므로 null을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "GET / (home page) route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET / (home page) route 테스트 통과.\n");
exit(0);
