<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 (태스크 0394, 0419, 0592, 0674, 0676, 0677, 0678, 0679, 0680, 0681, 0682).
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
 * 0678에서 `GET /install/database`(`InstallDBFormPage`)를 등록했다 — DB
 * 접속 정보(host/port/dbname/user/password) 입력 화면이다. 0679에서
 * `POST /install/database`(`DatabaseSetupHandler`)를 등록했다 — CSRF 토큰과
 * 입력값을 검증하고, 실제 접속을 시험해 성공할 때만 `config/local-config.php`에
 * 기록한다. 접속 실패/검증 실패 시에는 폼으로 되돌아가고 아무것도 기록하지
 * 않는다. 0680에서 `GET /install/schema`(`InstallSchemaApplyPage`)와
 * `POST /install/schema`(`SchemaApplyHandler`)를 등록했다 — 0679가 기록한
 * DB 설정을 0673 `AppBootstrap`으로 읽어 만든 PDO에 `SchemaApply`로
 * `db/schema`의 SQL을 FK 의존 순서로 적용한다. CSRF 검증 실패/DB 미접속/적용
 * 실패 시에는 오류를 표시하고 다음 단계로 넘어가지 않으며, 성공하면
 * `schema_version`이 채워진다. 0681에서 `GET /install/admin`
 * (`InstallAdminAccountFormPage`)과 `POST /install/admin`
 * (`AdminAccountSetupHandler`)을 등록했다 — 0673 `AppBootstrap`으로 얻은
 * PDO에 `AccountRepository`로 최초 관리자 계정을 생성한다. 비밀번호는
 * `password_hash()`로 해시해 `account` 테이블에 저장하며, CSRF 검증 실패/DB
 * 미접속/입력 검증 실패 시에는 폼으로 되돌아가고 계정을 생성하지 않는다.
 * 0682에서 `GET /install/complete`(`InstallCompletionHandler`)를 등록했다 —
 * `InstallerLock`(docroot 밖 `config/` 비공개 경로)으로 설치 완료를 기록하고
 * `InstallCompletionPage`를 보여준다. 위 `InstallerRouteGate` 생성 시에도
 * `InstallerLock::atDefaultPath()`를 전달해, lock 파일과 `schema_version` 중
 * 하나라도 설치 완료를 나타내면 이후 모든 `/install*` 접근을 차단하게 했다.
 * 0683에서 `GET /api/documents/by-title`(`DocumentApiRoutes`)을 등록했다 —
 * DB가 연결된 경우에만 `MintWiki\Document\PdoRepository`를 만들어 넘기고,
 * 미설정/오류 상태(`$pdo === null`)에서는 저장소 없이 등록해 핸들러가 503을
 * 반환하게 한다(0674 계약과 동일하게 죽지 않는다). 나머지
 * route(`docs/php-db-ui-micro-job-prompts-0351-0670.md`)는 이후 태스크에서
 * 이어진다.
 */

require __DIR__ . '/../vendor/autoload.php';

use MintWiki\App\AppBootstrap;
use MintWiki\App\ConfigLoader;
use MintWiki\Document\PdoRepository;
use MintWiki\Http\DocumentApiRoutes;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Installer\AdminAccountSetupHandler;
use MintWiki\Installer\DatabaseSetupHandler;
use MintWiki\Installer\InstallCompletionHandler;
use MintWiki\Installer\InstallerLock;
use MintWiki\Installer\InstallerRouteGate;
use MintWiki\Installer\RequirementCheck;
use MintWiki\Installer\SchemaApplyHandler;
use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\InstallAdminAccountFormPage;
use MintWiki\Ui\InstallDBFormPage;
use MintWiki\Ui\InstallRequiredPage;
use MintWiki\Ui\InstallSchemaApplyPage;
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
    $installerRouteGate = new InstallerRouteGate($pdo, null, InstallerLock::atDefaultPath());
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

// GET /install/database — DB 접속 정보 입력 화면 (태스크 0678). 설치가 이미
// 끝난 경우 위 InstallerRouteGate가 이 route에 도달하기 전에 403으로 막는다.
$router->register('GET', '/install/database', static function (): Response {
    $installDBFormPage = new InstallDBFormPage();

    return Response::html($installDBFormPage->render());
});

// POST /install/database — DB 접속 정보 제출 처리 (태스크 0679).
// CSRF 토큰과 입력값을 검증하고, 실제 접속을 시험한 뒤 성공할 때만
// `config/local-config.php`에 기록한다(`DatabaseSetupHandler` 참고).
// 접속 실패/검증 실패 시에는 폼으로 되돌아가 오류를 보여주고 아무것도
// 기록하지 않는다.
$router->register('POST', '/install/database', static function (): Response {
    $databaseSetupHandler = new DatabaseSetupHandler();

    return $databaseSetupHandler->handle($_POST);
});

// GET /install/schema — 스키마 적용 진행 화면 (태스크 0680). 설치가 이미 끝난
// 경우 위 InstallerRouteGate가 이 route에 도달하기 전에 403으로 막는다.
$router->register('GET', '/install/schema', static function (): Response {
    $installSchemaApplyPage = new InstallSchemaApplyPage();

    return Response::html($installSchemaApplyPage->render());
});

// POST /install/schema — 스키마 적용 처리 (태스크 0680). CSRF 토큰을 검증한 뒤
// `AppBootstrap`(0673)이 0679가 기록한 설정으로 만든 PDO에 `SchemaApply`로
// `db/schema`의 SQL을 FK 의존 순서로 적용한다. 실패 시에는 진행 화면으로
// 되돌아가 오류를 보여주고 다음 단계로 넘어가지 않는다.
$router->register('POST', '/install/schema', static function (): Response {
    $schemaApplyHandler = new SchemaApplyHandler();

    return $schemaApplyHandler->handle($_POST);
});

// GET /install/admin — 최초 관리자 계정 생성 화면 (태스크 0681). 설치가 이미
// 끝난 경우 위 InstallerRouteGate가 이 route에 도달하기 전에 403으로 막는다.
$router->register('GET', '/install/admin', static function (): Response {
    $installAdminAccountFormPage = new InstallAdminAccountFormPage();

    return Response::html($installAdminAccountFormPage->render());
});

// POST /install/admin — 관리자 계정 생성 처리 (태스크 0681). CSRF 토큰을
// 검증한 뒤 0673 `AppBootstrap`으로 얻은 PDO에 `AccountRepository`로 최초
// 관리자 계정을 생성한다. 비밀번호는 해시해 저장하며, 검증 실패/DB 미접속
// 시에는 폼으로 되돌아가 오류를 보여주고 계정을 생성하지 않는다.
$router->register('POST', '/install/admin', static function (): Response {
    $adminAccountSetupHandler = new AdminAccountSetupHandler();

    return $adminAccountSetupHandler->handle($_POST);
});

// GET /install/complete — 설치 완료 처리 및 안내 화면 (태스크 0682). 관리자 계정
// 생성(0681) 이후 이 route에 도달하면 `InstallerLock`(docroot 밖 `config/`
// 비공개 경로)으로 설치 완료를 기록해 재설치를 막고, `InstallCompletionPage`를
// 보여준다. 이후 요청부터는 위 `InstallerRouteGate`가 이 lock(또는
// schema_version)을 이유로 이 route를 포함한 모든 `/install*` 접근을 403으로
// 차단한다.
$router->register('GET', '/install/complete', static function (): Response {
    $installCompletionHandler = new InstallCompletionHandler();

    return $installCompletionHandler->handle();
});

// GET /api/documents, POST /api/documents, GET /api/documents/by-title
// (태스크 0683). DB가 연결된 경우에만 PdoRepository를 만들어 넘긴다 —
// 미설정/오류 상태에서는 저장소 없이 등록해 by-title 핸들러가 503을
// 반환하게 한다.
$documentRepository = $pdo !== null ? new PdoRepository($pdo) : null;
DocumentApiRoutes::register($router, $documentRepository);

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
