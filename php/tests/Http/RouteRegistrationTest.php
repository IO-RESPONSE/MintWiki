<?php

declare(strict_types=1);

/**
 * MintWiki\Http\Router::register()의 route 등록 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0397 RouterTest.php와 동일한 방식).
 *
 * RouterTest.php(0397)는 method/path가 일치할 때의 match() 동작을 검증한다.
 * 이 테스트는 register() 자체에 초점을 맞춰 — 여러 route를 독립적으로
 * 등록할 수 있는지, 같은 method+path로 재등록하면 핸들러가 교체되는지를
 * 확인한다. home("/")과 health("/health") placeholder route를 예시로 쓴다
 * (`public/index.php`의 0419 health endpoint, 0526 home page route 예고와
 * 동일한 이름을 사용해 이후 태스크와의 연결을 미리 드러낸다).
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

$failures = [];

$router = new Router();
$router->register('GET', '/', static fn (): Response => new Response(200, [], 'home placeholder'));
$router->register('GET', '/health', static fn (): Response => new Response(200, [], 'health placeholder'));

$homeHandler = $router->match(new Request('GET', '/'));
if ($homeHandler === null || $homeHandler()->body() !== 'home placeholder') {
    $failures[] = 'home("/")으로 등록한 route는 독립적으로 조회되어야 한다.';
}

$healthHandler = $router->match(new Request('GET', '/health'));
if ($healthHandler === null || $healthHandler()->body() !== 'health placeholder') {
    $failures[] = 'health("/health")로 등록한 route는 독립적으로 조회되어야 한다.';
}

$router->register('GET', '/health', static fn (): Response => new Response(200, [], 'health placeholder v2'));
$reRegisteredHealthHandler = $router->match(new Request('GET', '/health'));
if ($reRegisteredHealthHandler === null || $reRegisteredHealthHandler()->body() !== 'health placeholder v2') {
    $failures[] = '같은 method+path로 재등록하면 기존 핸들러를 교체해야 한다.';
}

$homeHandlerAfterReRegistration = $router->match(new Request('GET', '/'));
if ($homeHandlerAfterReRegistration === null || $homeHandlerAfterReRegistration()->body() !== 'home placeholder') {
    $failures[] = '다른 route의 재등록이 home("/") route에 영향을 주면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Route 등록 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Route 등록 테스트 통과.\n");
exit(0);
