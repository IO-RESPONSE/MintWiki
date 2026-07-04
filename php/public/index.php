<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 (태스크 0394, 0419, 0592, 0674, 0676, 0677).
 *
 * 0419부터 `/health` route를 등록했고, 0526에서 GET / (home page) route를
 * 추가했다. 0592에서는 라우팅되지 않은 요청에 대해 404 오류를 반환하도록
 * 수정했다 — API 요청은 JSON으로, UI 요청은 HTML로 구분해서 응답한다.
 * 0674에서 0673의 `AppBootstrap`을 연결해 PDO(또는 미설정/오류 상태)를
 * 얻는다 — DB 설정이 없거나 접속에 실패해도 치명적 오류로 죽지 않고
 * "미설정"/"오류" 상태로 취급해 `GET /`, `GET /health`가 계속 동작하게
 * 한다. 0676에서 `InstallerRouteGate`를 연결해, DB는 연결됐지만 아직
 * 설치(schema_version)가 끝나지 않은 상태에서는 요청을 `/install`로
 * 유도하고, 설치가 이미 끝난 상태에서는 installer 라우트 접근을 차단한다.
 * DB가 미설정/오류 상태이면(`$pdo === null`) 게이트를 아예 적용하지 않아
 * 0674 계약(`GET /`, `GET /health` 계속 동작)을 유지한다. 0677에서
 * `GET /install`(`InstallWelcomePage`)과 `GET /install/requirements`
 * (`RequirementCheck` + `InstallRequiredPage`)를 등록했다 — 설치가 이미
 * 끝난 경우 두 route 모두 위 `InstallerRouteGate`가 먼저 403으로 막는다.
 * 나머지 route(`docs/php-db-ui-micro-job-prompts-0351-0670.md`)는 이후
 * 태스크에서 이어진다.
 */

require __DIR__ . '/../vendor/autoload.php';

use MintWiki\App\AppBootstrap;
use MintWiki\App\ConfigLoader;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Installer\InstallerRouteGate;
use MintWiki\Installer\RequirementCheck;
use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\InstallRequiredPage;
use MintWiki\Ui\InstallWelcomePage;
use MintWiki\Ui\Layout;

/**
 * Response를 실제 HTTP 응답(상태 코드/헤더/본문)으로 내보낸다.
 */
function mintwiki_send_response(Response $response): void
{
    if (!headers_sent()) {
        http_response_code($response->status());
        foreach ($response->headers() as $name => $value) {
            header("{$name}: {$value}");
        }
    }

    echo $response->body();
}

$requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'CLI';
$requestUri = $_SERVER['REQUEST_URI'] ?? '/';
$requestPath = parse_url($requestUri, PHP_URL_PATH) ?? '/';
$isApiRequest = str_starts_with($requestPath, '/api/');

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

// 설치 게이트 (태스크 0676). DB가 연결된 경우에만 적용한다 — 미설정/오류
// 상태에서는 게이트를 건너뛰어 위 0674 계약을 지킨다.
if ($pdo !== null) {
    $installerRouteGate = new InstallerRouteGate($pdo);
    $gateResponse = $installerRouteGate->resolveFrontControllerResponse($requestPath, $isApiRequest);

    if ($gateResponse !== null) {
        mintwiki_send_response($gateResponse);

        return;
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

// GET /install — 설치 마법사 시작 화면 (태스크 0677). 설치가 이미 끝난
// 경우 위 InstallerRouteGate가 이 route에 도달하기 전에 403으로 막는다.
$router->register('GET', '/install', static function (): Response {
    $installWelcomePage = new InstallWelcomePage();

    return Response::html($installWelcomePage->render());
});

// GET /install/requirements — 시스템 요구사항 점검 화면 (태스크 0677).
// RequirementCheck의 검사 결과(누락된 확장/쓰기 불가 디렉터리)를 모아
// InstallRequiredPage에 전달한다. 검사 자체가 요청을 막지는 않는다 —
// 누락 사항이 있어도 안내 목록과 함께 200으로 화면을 보여준다.
$router->register('GET', '/install/requirements', static function (): Response {
    $requirementCheck = new RequirementCheck();
    $missingRequirements = [];

    try {
        $requirementCheck->areRequiredExtensionsLoaded();
    } catch (\RuntimeException $exception) {
        $missingRequirements[] = $exception->getMessage();
    }

    try {
        $requirementCheck->areRequiredDirectoriesWritable();
    } catch (\RuntimeException $exception) {
        $missingRequirements[] = $exception->getMessage();
    }

    $installRequiredPage = new InstallRequiredPage();

    return Response::html($installRequiredPage->render($missingRequirements));
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

    mintwiki_send_response($response);

    return;
}

// 라우팅되지 않은 요청에 대한 오류 응답 (태스크 0592).
// API 요청은 JSON으로, UI 요청은 HTML로 응답한다.
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

mintwiki_send_response($response);
