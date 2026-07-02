<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 (태스크 0394, 0419).
 *
 * 0419부터 `/health` route를 등록했고, 0526에서 GET / (home page) route를
 * 추가했다 — 그 외 path/method는 여전히 라우팅 없이 고정된 placeholder
 * 응답을 반환한다. 나머지 route (`docs/php-db-ui-micro-job-prompts-0351-0670.md`)
 * 는 이후 태스크에서 이어진다.
 */

require __DIR__ . '/../vendor/autoload.php';

use MintWiki\App\ConfigLoader;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Ui\Layout;

$requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'CLI';
$requestUri = $_SERVER['REQUEST_URI'] ?? '/';
$requestPath = parse_url($requestUri, PHP_URL_PATH) ?? '/';

$router = new Router();

// GET / — 문서 검색 진입점 (태스크 0526)
$router->register('GET', '/', static function (): Response {
    $layout = new Layout();
    $body = '<main>'
        . '<h1>문서 검색</h1>'
        . '<form method="get" action="/api/documents/by-title">'
        . '<input type="text" name="q" placeholder="검색어를 입력하세요" required>'
        . '<button type="submit">검색</button>'
        . '</form>'
        . '</main>';

    return Response::html($layout->render('MintWiki', $body));
});

// GET /health — 헬스체크 (태스크 0419)
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
