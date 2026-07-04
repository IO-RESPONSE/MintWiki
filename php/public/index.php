<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 (태스크 0394, 0419, 0592, 0674).
 *
 * 0419부터 `/health` route를 등록했고, 0526에서 GET / (home page) route를
 * 추가했다. 0592에서는 라우팅되지 않은 요청에 대해 404 오류를 반환하도록
 * 수정했다 — API 요청은 JSON으로, UI 요청은 HTML로 구분해서 응답한다.
 * 0674에서 0673의 `AppBootstrap`을 연결해 PDO(또는 미설정/오류 상태)를
 * 얻는다 — DB 설정이 없거나 접속에 실패해도 치명적 오류로 죽지 않고
 * "미설정"/"오류" 상태로 취급해 `GET /`, `GET /health`가 계속 동작하게
 * 한다. 나머지 route (`docs/php-db-ui-micro-job-prompts-0351-0670.md`)는
 * 이후 태스크에서 이어진다.
 */

require __DIR__ . '/../vendor/autoload.php';

use MintWiki\App\AppBootstrap;
use MintWiki\App\ConfigLoader;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Ui\Layout;
use MintWiki\Ui\ErrorPage;

$requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'CLI';
$requestUri = $_SERVER['REQUEST_URI'] ?? '/';
$requestPath = parse_url($requestUri, PHP_URL_PATH) ?? '/';

// DB 설정/연결 상태 판단 (태스크 0674). connectionConfig()가 null이면
// "미설정", 설정은 있으나 실제 접속(pdo())이 예외를 던지면 "오류"로
// 취급한다 — 두 경우 모두 index.php를 죽이지 않는다.
$dbStatus = 'unconfigured';
$pdo = null;

$bootstrap = new AppBootstrap();
if ($bootstrap->connectionConfig() !== null) {
    try {
        $pdo = $bootstrap->pdo();
        $dbStatus = 'connected';
    } catch (\Throwable $exception) {
        $dbStatus = 'error';
    }
}

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

// GET /health — 헬스체크 (태스크 0419, DB 상태 필드는 0674)
$router->register('GET', '/health', static function () use ($dbStatus): Response {
    $config = new ConfigLoader();

    return Response::json([
        'status' => 'ok',
        'app' => $config->get('app_name', 'wiki-engine'),
        'db' => $dbStatus,
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

// 라우팅되지 않은 요청에 대한 오류 응답 (태스크 0592).
// API 요청은 JSON으로, UI 요청은 HTML로 응답한다.
$isApiRequest = str_starts_with($requestPath, '/api/');

if ($isApiRequest) {
    $response = Response::json([
        'error' => 'not_found',
        'message' => 'The requested resource was not found.',
        'path' => $requestPath,
    ], 404);
} else {
    $errorPage = new ErrorPage();
    $html = $errorPage->renderNotFound($requestPath);
    $response = Response::html($html, 404);
}

if (!headers_sent()) {
    http_response_code($response->status());
    foreach ($response->headers() as $name => $value) {
        header("{$name}: {$value}");
    }
}

echo $response->body();
