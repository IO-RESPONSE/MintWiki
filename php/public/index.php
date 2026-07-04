<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 (태스크 0394, 0419, 0592, 0674, 0676, 0677, 0678, 0679, 0680, 0681, 0682, 0683, 0684).
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
 * 반환하게 한다(0674 계약과 동일하게 죽지 않는다). 0684에서
 * `GET /wiki/{title}`을 등록했다 — 동적 라우터(0675)로 title 세그먼트를
 * 얻어 `Document\Service`(위 `$documentRepository`)로 문서를 조회하고
 * `DocumentViewPage`(`Layout` 재사용)로 렌더링한다. 문서가 없거나
 * `$documentRepository === null`(DB 미설정/오류)이면 "문서 없음 + 만들기
 * 링크"를 담은 404 HTML을 반환한다. 0685에서 `GET/POST /wiki/{title}/edit`을
 * 등록했다 — `Revision\PdoRepository`(신규)를 `$revisionRepository`로 만들어
 * 문서 생성/편집 시 새 리비전을 실제로 기록한다. `GET`은 문서가 있으면 현재
 * 리비전의 source로, 없으면 빈 새 문서 폼으로 `DocumentEditorPage`를 보여준다.
 * `POST`는 CSRF 토큰(`CsrfTokenService`)을 검증하고, 제목/본문이 비어있으면
 * 폼으로 되돌려 오류를 보여준다. 통과하면 `Document\Service`로 문서를
 * 생성/갱신하고 `Revision\Repository`로 새 리비전을 만든 뒤 문서의
 * `currentRevisionId`를 그 리비전으로 갱신한다(0029 create-first-revision과
 * 동일한 순서: 문서 생성/조회 -> 리비전 생성 -> 문서에 리비전 연결). 저장에
 * 성공하면 `GET /wiki/{title}`로 302 리다이렉트한다. `$documentRepository`나
 * `$revisionRepository`가 없으면(DB 미설정/오류) 폼으로 되돌아가 503을
 * 반환한다. 0686에서 `GET`/`POST /login`, `GET`/`POST /logout`을 등록했다 —
 * `LoginHandler`가 CSRF 토큰과 `account` 테이블의 password_hash를 대조해
 * 성공 시 `PhpSessionAdapter`에 계정 id를 저장하고(`SessionUserResolver`가
 * 이후 요청에서 이 id로 로그인 사용자를 복원한다), `LogoutHandler`가 세션을
 * 파기한다. 이미 로그인된 상태에서 `GET /login`에 접근하면 폼을 다시 보여주지
 * 않고 홈으로 리다이렉트해 세션 복원이 실제로 동작함을 드러낸다. DB
 * 미설정(`$accountRepository === null`)이면 로그인 여부를 판단할 수 없으므로
 * `GET /login`은 항상 폼을 보여주고, `POST /login`은 503을 반환한다. 나머지
 * route(`docs/php-db-ui-micro-job-prompts-0351-0670.md`)는 이후 태스크에서
 * 이어진다.
 */

require __DIR__ . '/../vendor/autoload.php';

use MintWiki\App\AppBootstrap;
use MintWiki\App\ConfigLoader;
use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\PdoRepository;
use MintWiki\Document\Service as DocumentService;
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
use MintWiki\Revision\PdoRepository as RevisionPdoRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\LoginHandler;
use MintWiki\Security\LogoutHandler;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\DocumentEditorPage;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\InstallAdminAccountFormPage;
use MintWiki\Ui\InstallDBFormPage;
use MintWiki\Ui\InstallRequiredPage;
use MintWiki\Ui\InstallSchemaApplyPage;
use MintWiki\Ui\InstallWelcomePage;
use MintWiki\Ui\Layout;
use MintWiki\Ui\LoginPage;
use MintWiki\User\AccountRepository;

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

/**
 * UUID v4 문자열을 생성한다 (리비전 id 발급용, 태스크 0685).
 */
function mintwiki_generate_uuid_v4(): string
{
    $bytes = random_bytes(16);
    $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
    $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);
    $hex = bin2hex($bytes);

    return sprintf(
        '%s-%s-%s-%s-%s',
        substr($hex, 0, 8),
        substr($hex, 8, 4),
        substr($hex, 12, 4),
        substr($hex, 16, 4),
        substr($hex, 20, 12)
    );
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
$revisionRepository = $pdo !== null ? new RevisionPdoRepository($pdo) : null;
DocumentApiRoutes::register($router, $documentRepository);

// GET/POST /login, GET/POST /logout (태스크 0686). $accountRepository는
// $pdo가 연결된 경우에만 만들어, 로그인 상태 확인/자격 증명 대조에 쓴다.
$accountRepository = $pdo !== null ? new AccountRepository($pdo) : null;
$sessionAdapter = new PhpSessionAdapter();

$router->register('GET', '/login', static function () use ($accountRepository, $sessionAdapter): Response {
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return new Response(302, ['Location' => '/']);
        }
    }

    $loginPage = new LoginPage();

    return Response::html($loginPage->render());
});

$router->register('POST', '/login', static function (): Response {
    $loginHandler = new LoginHandler();

    return $loginHandler->handle($_POST);
});

$logoutRouteHandler = static function (): Response {
    $logoutHandler = new LogoutHandler();

    return $logoutHandler->handle();
};
$router->register('GET', '/logout', $logoutRouteHandler);
$router->register('POST', '/logout', $logoutRouteHandler);

// GET /wiki/{title} — 문서 보기 (태스크 0684, 리비전 source 연결은 0685).
// 동적 라우터(0675)로 등록해 title 세그먼트를 얻고, Document\Service(+ 위
// documentRepository)로 문서를 조회해 DocumentViewPage(Layout 재사용)로
// HTML을 렌더링한다. 문서가 없거나 DB가 미설정/오류 상태
// (documentRepository === null)이면 "문서 없음 + 만들기 링크"를 담은 404
// HTML을 반환해 죽지 않는다. 0685에서 revisionRepository가 생겼으므로
// currentRevisionId가 있으면 그 리비전의 source를 함께 렌더링한다.
$router->register('GET', '/wiki/{title}', static function (array $params) use ($documentRepository, $revisionRepository): Response {
    $documentViewPage = new DocumentViewPage();
    $requestedTitle = rawurldecode($params['title'] ?? '');

    if ($documentRepository === null) {
        return Response::html($documentViewPage->render(null, null, $requestedTitle), 404);
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html($documentViewPage->render(null, null, $requestedTitle), 404);
    }

    $source = null;
    if ($revisionRepository !== null && $document->currentRevisionId() !== null) {
        $source = $revisionRepository->get($document->currentRevisionId())?->source();
    }

    return Response::html($documentViewPage->render($document, $source));
});

// GET/POST /wiki/{title}/edit — 문서 생성/편집 (태스크 0685). DocumentEditorPage로
// 제목·본문·CSRF 토큰이 있는 폼을 렌더링한다. GET은 문서가 있으면 현재
// 리비전의 source로 미리 채우고, 없으면 빈 새 문서 폼으로 동작한다. POST는
// CSRF 토큰을 검증하고(실패 시 403), 제목/본문이 비어있으면 폼으로 되돌려
// 오류를 보여준다(422). 통과하면 Document\Service로 문서를 생성/갱신하고
// Revision\Repository로 새 리비전을 만든 뒤 문서의 currentRevisionId를 그
// 리비전으로 연결한다(0029 create-first-revision과 동일한 순서). 저장에
// 성공하면 GET /wiki/{title}로 302 리다이렉트한다. documentRepository나
// revisionRepository가 없으면(DB 미설정/오류) 폼으로 되돌아가 503을
// 반환해 죽지 않는다.
$router->register('GET', '/wiki/{title}/edit', static function (array $params) use ($documentRepository, $revisionRepository): Response {
    $documentEditorPage = new DocumentEditorPage();
    $requestedTitle = rawurldecode($params['title'] ?? '');

    if ($documentRepository === null) {
        return Response::html($documentEditorPage->render($requestedTitle, $requestedTitle, '', true));
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html($documentEditorPage->render($requestedTitle, $requestedTitle, '', true));
    }

    $source = '';
    if ($revisionRepository !== null && $document->currentRevisionId() !== null) {
        $source = $revisionRepository->get($document->currentRevisionId())?->source() ?? '';
    }

    return Response::html($documentEditorPage->render($requestedTitle, $document->title(), $source, false));
});

$router->register('POST', '/wiki/{title}/edit', static function (array $params) use ($documentRepository, $revisionRepository): Response {
    $documentEditorPage = new DocumentEditorPage();
    $csrfTokenService = new CsrfTokenService();
    $requestedTitle = rawurldecode($params['title'] ?? '');

    $titleInput = is_string($_POST['title'] ?? null) ? $_POST['title'] : '';
    $sourceInput = is_string($_POST['source'] ?? null) ? $_POST['source'] : '';
    $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

    if ($documentRepository === null || $revisionRepository === null) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, true, [
                '_form' => '데이터베이스가 설정되지 않아 저장할 수 없습니다.',
            ]),
            503
        );
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $existingDocument = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $existingDocument = null;
    }
    $isNew = $existingDocument === null;

    if (!$csrfTokenService->validate($csrfToken)) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                '_form' => '유효하지 않은 요청입니다. 다시 시도하세요.',
            ]),
            403
        );
    }

    $validationErrors = [];
    if (trim($titleInput) === '') {
        $validationErrors['title'] = '제목을 입력하세요.';
    }
    if (trim($sourceInput) === '') {
        $validationErrors['source'] = '내용을 입력하세요.';
    }

    if ($validationErrors !== []) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, $validationErrors),
            422
        );
    }

    try {
        if ($existingDocument === null) {
            $document = $documentService->create($titleInput);
            $parentRevisionId = null;
        } else {
            $document = $existingDocument;
            if ($document->title() !== $titleInput) {
                $document = $documentService->update(new Document($document->id(), $titleInput, $document->currentRevisionId()));
            }
            $parentRevisionId = $document->currentRevisionId();
        }

        $revision = $revisionRepository->create(new Revision(
            mintwiki_generate_uuid_v4(),
            $document->id(),
            $sourceInput,
            '',
            '',
            $parentRevisionId
        ));

        $document = $documentService->update(new Document($document->id(), $document->title(), $revision->id()));
    } catch (EmptyTitleError) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                'title' => '제목을 입력하세요.',
            ]),
            422
        );
    } catch (DuplicateNormalizedTitleError) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                'title' => '이미 존재하는 제목입니다.',
            ]),
            409
        );
    }

    return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title())]);
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
