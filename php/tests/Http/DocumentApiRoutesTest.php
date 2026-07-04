<?php

declare(strict_types=1);

/**
 * `MintWiki\Http\DocumentApiRoutes::register()`의 동작을 확인하는 smoke
 * test. phpunit 없이 `php` CLI만으로 실행된다(0398 RouteRegistrationTest.php,
 * 0419 HealthRouteTest.php와 동일한 방식).
 *
 * `GET`/`POST /api/documents`는 여전히 저장소/서비스 연결 없이 501 JSON
 * 계약만 지키는지 확인한다 — 실제 문서 생성/목록 조회 동작은 검증 대상이
 * 아니다. `GET /api/documents/by-title`은 0683에서 실제 조회 동작으로
 * 바뀌었으므로 `DocumentByTitleRouteTest.php`가 별도로 검증한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Http\DocumentApiRoutes;
use MintWiki\Http\Request;
use MintWiki\Http\Router;

$failures = [];

$router = new Router();
DocumentApiRoutes::register($router);

$routesUnderTest = [
    ['GET', '/api/documents'],
    ['POST', '/api/documents'],
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

// GET /api/documents/by-title는 등록되어 있지만(0683), 저장소를 주입하지
// 않으면(register()의 기본값) DB 미설정으로 간주해 503을 반환해야 한다 —
// 성공/미존재 조회 동작은 DocumentByTitleRouteTest.php가 검증한다.
$byTitleHandler = $router->match(new Request('GET', '/api/documents/by-title'));
if ($byTitleHandler === null) {
    $failures[] = 'GET /api/documents/by-title route는 등록되어 있어야 한다.';
} else {
    $byTitleResponse = $byTitleHandler();
    if ($byTitleResponse->status() !== 503) {
        $failures[] = '저장소가 주입되지 않은 GET /api/documents/by-title는 503을 반환해야 한다.';
    }
}

// 등록되지 않은 method/path는 여전히 매칭되지 않아야 한다.
if ($router->match(new Request('DELETE', '/api/documents')) !== null) {
    $failures[] = 'DELETE /api/documents는 등록되어 있지 않으므로 null을 반환해야 한다.';
}
if ($router->match(new Request('GET', '/api/documents/some-id')) !== null) {
    $failures[] = 'GET /api/documents/some-id(동적 세그먼트)는 아직 등록되어 있지 않으므로 null을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "문서 API placeholder route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "문서 API placeholder route 테스트 통과.\n");
exit(0);
