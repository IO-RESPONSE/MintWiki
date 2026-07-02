<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 (태스크 0394, 0419).
 *
 * 0419부터 `/health` route 하나만 Router에 연결된다 — 그 외 path/method는
 * 여전히 라우팅 없이 고정된 placeholder 응답을 반환한다. 나머지 route
 * (0526 home page route 등, `docs/php-db-ui-micro-job-prompts-0351-0670.md`)
 * 는 이후 태스크에서 이어진다.
 */

require __DIR__ . '/../vendor/autoload.php';

use MintWiki\App\ConfigLoader;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;

$requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'CLI';
$requestUri = $_SERVER['REQUEST_URI'] ?? '/';
$requestPath = parse_url($requestUri, PHP_URL_PATH) ?? '/';

$router = new Router();
$router->register('GET', '/health', static function (): Response {
    $config = new ConfigLoader();

    return Response::json([
        'status' => 'ok',
        'app' => $config->get('app_name', 'wiki-engine'),
    ]);
});

$handler = $router->match(new Request($requestMethod, $requestPath));

if ($handler !== null) {
    $response = $handler();

    if (!headers_sent()) {
        http_response_code($response->status());
        foreach ($response->headers() as $name => $value) {
            header("{$name}: {$value}");
        }
    }

    echo $response->body();

    return;
}

$body = sprintf(
    "MintWiki PHP front controller placeholder\nmethod=%s\nuri=%s\n",
    $requestMethod,
    $requestUri
);

if (!headers_sent()) {
    header('Content-Type: text/plain; charset=utf-8');
    http_response_code(200);
}

echo $body;
