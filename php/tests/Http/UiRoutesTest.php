<?php

declare(strict_types=1);

/**
 * `MintWiki\Http\UiRoutes::register()`의 동작을 확인하는 smoke
 * test. phpunit 없이 `php` CLI만으로 실행된다(0420 DocumentApiRoutesTest.php와
 * 동일한 방식).
 *
 * UI route들(sitemap 등)의 등록을 확인한다. 모든 route가 501 JSON 계약을
 * 지키는지 검증한다 — 실제 sitemap 생성 로직은 검증 대상이 아니다.
 * `public/index.php`에 연결하는 것은 이 태스크의 범위 밖이라 프론트
 * 컨트롤러는 건드리지 않는다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\UiRoutes;
use MintWiki\Http\Request;
use MintWiki\Http\Router;

$failures = [];

$router = new Router();
UiRoutes::register($router);

$routesUnderTest = [
    ['GET', '/sitemap.xml'],
];

foreach ($routesUnderTest as [$method, $path]) {
    $handler = $router->match(new Request($method, $path));
    if ($handler === null) {
        $failures[] = "{$method} {$path} route는 등록되어 있어야 한다.";
        continue;
    }

    $response = $handler();
    if ($response->status() !== 501) {
        $failures[] = "{$method} {$path} 응답의 status는 501이어야 한다.";
    }
    if ($response->headers() !== ['Content-Type' => 'application/json']) {
        $failures[] = "{$method} {$path} 응답의 Content-Type은 application/json이어야 한다.";
    }
    if ($response->body() !== '{"error":"not_implemented"}') {
        $failures[] = "{$method} {$path} 응답 body는 not_implemented 계약을 담아야 한다.";
    }
}

// 등록되지 않은 method/path는 여전히 매칭되지 않아야 한다.
if ($router->match(new Request('POST', '/sitemap.xml')) !== null) {
    $failures[] = 'POST /sitemap.xml는 등록되어 있지 않으므로 null을 반환해야 한다.';
}
if ($router->match(new Request('GET', '/sitemap')) !== null) {
    $failures[] = 'GET /sitemap는 등록되어 있지 않으므로 null을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "UI route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "UI route 테스트 통과.\n");
exit(0);
