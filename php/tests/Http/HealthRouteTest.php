<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0419에서 등록하는 `/health` route 핸들러의
 * 동작을 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다
 * (0398 RouteRegistrationTest.php와 동일한 방식).
 *
 * 실제 HTTP 서버를 띄워 프론트 컨트롤러를 검증하는 것은
 * `tests/test_php_public_front_controller.py`(파이썬, `php -S`)의 몫이다.
 * 이 테스트는 그 핸들러가 만드는 `Response`가 status/Content-Type/body를
 * 올바르게 채우는지만 `Router` + `ConfigLoader`를 직접 조합해 확인한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\App\ConfigLoader;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;

$failures = [];

$router = new Router();
$router->register('GET', '/health', static function (): Response {
    $config = new ConfigLoader();

    return Response::json([
        'status' => 'ok',
        'app' => $config->get('app_name', 'wiki-engine'),
    ]);
});

// (1) 기본 app 이름("wiki-engine")과 status("ok")를 반환해야 한다.
$handler = $router->match(new Request('GET', '/health'));
if ($handler === null) {
    $failures[] = '/health route는 등록되어 있어야 한다.';
} else {
    $response = $handler();
    if ($response->status() !== 200) {
        $failures[] = '/health 응답의 status는 200이어야 한다.';
    }
    if ($response->headers() !== ['Content-Type' => 'application/json']) {
        $failures[] = '/health 응답의 Content-Type은 application/json이어야 한다.';
    }
    if ($response->body() !== '{"status":"ok","app":"wiki-engine"}') {
        $failures[] = '/health 응답 body는 기본 app 이름과 status를 담아야 한다.';
    }
}

// (2) WIKI_APP_NAME 환경변수가 있으면 그 값을 app 이름으로 반환해야 한다.
putenv('WIKI_APP_NAME=custom-wiki');
$handlerWithEnv = $router->match(new Request('GET', '/health'));
$responseWithEnv = $handlerWithEnv === null ? null : $handlerWithEnv();
if ($responseWithEnv === null || $responseWithEnv->body() !== '{"status":"ok","app":"custom-wiki"}') {
    $failures[] = 'WIKI_APP_NAME 환경변수가 설정되어 있으면 그 값을 app 이름으로 반환해야 한다.';
}
putenv('WIKI_APP_NAME');

// (3) 등록되지 않은 다른 method/path는 여전히 매칭되지 않아야 한다.
if ($router->match(new Request('POST', '/health')) !== null) {
    $failures[] = 'POST /health는 등록되어 있지 않으므로 null을 반환해야 한다.';
}
if ($router->match(new Request('GET', '/other')) !== null) {
    $failures[] = 'GET /other는 등록되어 있지 않으므로 null을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "/health route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "/health route 테스트 통과.\n");
exit(0);
