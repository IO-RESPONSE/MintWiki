<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 (태스크 0394, 0419, 0592, 0674, 0676, 0677, 0678, 0679, 0680, 0681, 0682, 0683, 0684, 0687, 0691).
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
 * `GET /login`은 항상 폼을 보여주고, `POST /login`은 503을 반환한다. 0687에서
 * `GET /wiki/{title}`과 `GET`/`POST /wiki/{title}/edit`에 ACL 검사를
 * 추가했다 — `Acl\PdoRepository`로 `acl_rule`/`acl_namespace_rule`을 읽어
 * `Acl\AclService`를 구성하고(네임스페이스 기본 규칙이 DB에 없으면
 * `Acl\DefaultPolicy`로 대체), `SessionUserResolver`로 복원한 현재 사용자를
 * ACL subject(로그인 사용자면 USER, 아니면 ANONYMOUS)로 매핑해 read/edit
 * 권한을 확인한다. 문서 보기는 거부되면 `PermissionDeniedPage`로 403을
 * 반환하고, 편집 GET/POST는 익명 사용자면 `/login`으로 302 리다이렉트하고
 * 로그인한 사용자면 403을 반환한다. 0691에서 `mintwiki_build_layout()`을
 * 추가했다 — 요청 경로와 세션의 로그인 사용자로 `NavigationBar`(0690)를
 * 렌더링해 `Layout`의 header에 주입한다. `GET /`, `GET`/`POST /login`,
 * `GET /wiki/{title}`, `GET`/`POST /wiki/{title}/edit`와 404 fallback이 이
 * `Layout` 인스턴스를 재사용해 상단 네비게이션 바를 일관되게 보여준다.
 * navigation 메뉴 항목은 아직 비어있고(브랜드/검색/로그인 상태만 표시),
 * 실제 메뉴 구성은 이후 태스크에서 채운다. 0693에서 `GET /`가 인라인
 * 검색 폼 대신 `FrontPage`(검색 영역 + 최근 편집된 문서 목록 + 사이트
 * 소개)를 렌더링하도록 개편했다 — 최근 문서 목록은 `RecentDocumentsQuery`로
 * DB가 연결된 경우에만 조회하고, 미설정/오류 상태에서는 빈 목록으로
 * 대체해 `FrontPage`가 빈 상태 안내를 보여주게 한다. 0697에서
 * `GET /admin`(관리자 콘솔 진입점)을 등록했다 — 0696 `AdminAccessGate`로
 * 익명은 `/login`으로 302, 비관리자는 403으로 먼저 걸러내고, 관리자만
 * `AdminDashboardPage`(0691 `Layout` 재사용)를 보게 한다. 대시보드는 이후
 * 태스크(0698-0702)가 등록할 관리 하위 화면(감사 로그/신고/사용자 차단/
 * 유지보수/백업·복원/진단) 링크 목록을 보여준다. 0698에서
 * `GET /admin/audit`(감사 로그 뷰어)을 등록했다 — 동일한 0696
 * `AdminAccessGate`로 인가를 확인한 뒤, `$pdo`가 연결된 경우에만
 * `RecentAuditEventsQuery`로 `audit_event` 테이블의 최근 이벤트(최대
 * 100건)를 조회해 `AuditViewerPage`(`AuditRow` 재사용)에 주입한다.
 * 미설정/오류/조회 실패 시에는 빈 목록으로 대체해 빈 상태를 보여준다.
 * 나머지 route(`docs/php-db-ui-micro-job-prompts-0351-0670.md`)는 이후
 * 태스크에서 이어진다.
 */

require __DIR__ . '/../vendor/autoload.php';

use MintWiki\Acl\AclService;
use MintWiki\Acl\DefaultPolicy;
use MintWiki\Acl\NamespaceAclDefaults;
use MintWiki\Acl\PdoRepository as AclPdoRepository;
use MintWiki\Acl\Permission as AclPermission;
use MintWiki\Acl\SubjectType as AclSubjectType;
use MintWiki\App\AppBootstrap;
use MintWiki\App\ConfigLoader;
use MintWiki\Audit\RecentAuditEventsQuery;
use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\PdoRepository;
use MintWiki\Document\RecentDocumentsQuery;
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
use MintWiki\Security\AdminAccessGate;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\LoginHandler;
use MintWiki\Security\LogoutHandler;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\AdminDashboardPage;
use MintWiki\Ui\AuditViewerPage;
use MintWiki\Ui\DocumentEditorPage;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\FrontPage;
use MintWiki\Ui\InstallAdminAccountFormPage;
use MintWiki\Ui\InstallDBFormPage;
use MintWiki\Ui\InstallRequiredPage;
use MintWiki\Ui\InstallSchemaApplyPage;
use MintWiki\Ui\InstallWelcomePage;
use MintWiki\Ui\Layout;
use MintWiki\Ui\LoginPage;
use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationBar;
use MintWiki\Ui\PermissionDeniedPage;
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
 * 현재 요청의 ACL 검사 대상(subject)을 결정한다 (태스크 0687).
 *
 * 세션(0686 `SessionUserResolver`)에 로그인한 사용자가 있으면
 * AclSubjectType::User와 계정 id를, 없으면(비로그인, DB 미설정/오류) 항상
 * AclSubjectType::Anonymous를 반환한다.
 *
 * @return array{0: AclSubjectType, 1: ?string}
 */
function mintwiki_resolve_acl_subject(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): array
{
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return [AclSubjectType::User, $currentUser->id()];
        }
    }

    return [AclSubjectType::Anonymous, null];
}

/**
 * 현재 요청 경로/로그인 상태를 반영한 상단 네비게이션 바를 헤더에 포함한
 * Layout을 만든다 (태스크 0691). 메뉴 항목(Navigation)은 아직 비어있다 —
 * 실제 메뉴 구성은 이후 태스크(0692+)에서 채운다. NavigationBar는
 * $accountRepository가 없거나(DB 미설정/오류) 세션에 로그인 사용자가 없으면
 * 자동으로 로그아웃 상태로 렌더링한다.
 */
function mintwiki_build_layout(string $requestPath, ?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): Layout
{
    $currentUser = $accountRepository !== null
        ? (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve()
        : null;

    $headerContent = (new NavigationBar())->render(new Navigation(), $requestPath, [], $currentUser);

    return new Layout(null, $headerContent);
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

// 로그인 세션 (태스크 0686). $accountRepository는 $pdo가 연결된 경우에만
// 만든다. 0691에서 위치를 앞당겼다 — 상단 네비게이션 바(로그인/로그아웃
// 상태 표시)가 GET / 등 모든 route에서 필요하기 때문이다.
$accountRepository = $pdo !== null ? new AccountRepository($pdo) : null;
$sessionAdapter = new PhpSessionAdapter();

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

// GET / — 나무위키식 대문(프론트페이지) (태스크 0526, 상단 네비게이션 바
// 연결은 0691, 대문 개편은 0693). FrontPage(검색 영역 + 최근 편집된 문서
// 목록 + 사이트 소개)를 Layout(0691 스킨) 위에 렌더링한다. 최근 문서
// 목록은 DB가 연결된 경우에만 RecentDocumentsQuery로 조회하고, 미설정/
// 오류 상태(schema 미적용 포함)에서는 빈 목록으로 대체해 FrontPage가
// 안전하게 빈 상태 안내를 보여주게 한다 — 0674 계약(GET /가 죽지 않음)과
// 동일한 판단이다.
$router->register('GET', '/', static function () use ($accountRepository, $sessionAdapter, $pdo): Response {
    $layout = mintwiki_build_layout('/', $accountRepository, $sessionAdapter);
    $frontPage = new FrontPage(null, $layout);

    $recentDocuments = [];
    if ($pdo !== null) {
        try {
            $recentDocuments = (new RecentDocumentsQuery($pdo))->listRecentlyUpdated();
        } catch (\Throwable $exception) {
            $recentDocuments = [];
        }
    }

    return Response::html($frontPage->render($recentDocuments));
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

// GET/POST /login, GET/POST /logout (태스크 0686). $accountRepository/
// $sessionAdapter는 위에서(태스크 0691) 앞당겨 정의했다 — 로그인 상태
// 확인/자격 증명 대조에 그대로 쓴다.

// ACL (태스크 0687). 문서별 규칙(acl_rule)이 있으면 AclService가 그것만
// 쓰고, 없으면 네임스페이스 기본 규칙(acl_namespace_rule)으로 대체한다.
// DEFAULT_NAMESPACE("*")에 DB 규칙이 아직 없으면(신규 설치, seed 데이터
// 없음) `DefaultPolicy`(공개 읽기 허용/익명 편집 거부/로그인 사용자 편집
// 허용)로 대체해 문서가 계속 정상 동작하게 한다.
// 0688 라이브 smoke test에서 발견: DB는 연결됐지만 아직 schema가 적용되지
// 않은 상태(설치 마법사가 `/install/database`까지만 끝낸 상태)에서는
// `acl_namespace_rule` 테이블이 없어 이 조회가 예외를 던진다 — try/catch
// 없이는 `/install/schema`, `/install/admin` 등 나머지 모든 route가 이
// 코드에서 502/500으로 죽어 설치 마법사 자체를 끝까지 진행할 수 없었다.
$aclRuleRepository = $pdo !== null ? new AclPdoRepository($pdo) : null;
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
if ($aclRuleRepository !== null) {
    try {
        $dbNamespaceRules = $aclRuleRepository->namespaceRules(NamespaceAclDefaults::DEFAULT_NAMESPACE);
        if ($dbNamespaceRules !== []) {
            $namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, $dbNamespaceRules);
        }
    } catch (\Throwable $exception) {
        // schema 미적용 상태 — DefaultPolicy로 계속 진행한다.
    }
}
$aclService = new AclService($namespaceAclDefaults);

$router->register('GET', '/login', static function () use ($accountRepository, $sessionAdapter): Response {
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return new Response(302, ['Location' => '/']);
        }
    }

    $layout = mintwiki_build_layout('/login', $accountRepository, $sessionAdapter);
    $loginPage = new LoginPage(null, $layout);

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

// GET /wiki/{title} — 문서 보기 (태스크 0684, 리비전 source 연결은 0685,
// ACL 적용은 0687, 나무위키식 헤더/액션 탭은 0692). 동적 라우터(0675)로
// 등록해 title 세그먼트를 얻고, Document\Service(+ 위 documentRepository)로
// 문서를 조회해 DocumentViewPage(Layout 재사용)로 HTML을 렌더링한다. 문서가
// 없거나 DB가 미설정/오류 상태(documentRepository === null)이면 나무위키식
// 빈 문서 안내(제목 + 편집 링크)를 담은 404 HTML을 반환해 죽지 않는다.
// 0685에서 revisionRepository가 생겼으므로 currentRevisionId가 있으면 그
// 리비전의 source를 함께 렌더링한다. 0687에서 문서가 존재하는 경우
// AclService로 현재 사용자(0686 세션)의 read 권한을 확인해, 거부되면
// PermissionDeniedPage로 403을 반환한다 — 존재하지 않는 문서는 보호할
// 대상이 없으므로 검사하지 않는다. 0692에서 $requestPath를 그대로 전달해
// DocumentViewPage가 액션 탭의 활성 상태를 판단하게 하고, 현재 리비전의
// authorId를 "마지막 편집" 메타 정보로 함께 넘긴다(비어있으면 생략된다).
$router->register('GET', '/wiki/{title}', static function (array $params) use (
    $documentRepository,
    $revisionRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter);
    $documentViewPage = new DocumentViewPage(null, $layout);
    $requestedTitle = rawurldecode($params['title'] ?? '');

    if ($documentRepository === null) {
        return Response::html($documentViewPage->render(null, null, $requestedTitle, $requestPath), 404);
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html($documentViewPage->render(null, null, $requestedTitle, $requestPath), 404);
    }

    $documentAcl = $aclRuleRepository?->documentAcl($document->id());
    [$subjectType, $subjectId] = mintwiki_resolve_acl_subject($accountRepository, $sessionAdapter);
    $decision = $aclService->check(AclPermission::Read, $subjectType, $subjectId, $documentAcl);

    if ($decision->isDenied()) {
        $permissionDeniedPage = new PermissionDeniedPage(null, $layout);

        return Response::html($permissionDeniedPage->render($decision), 403);
    }

    $source = null;
    $lastEditedBy = null;
    if ($revisionRepository !== null && $document->currentRevisionId() !== null) {
        $currentRevision = $revisionRepository->get($document->currentRevisionId());
        $source = $currentRevision?->source();
        $lastEditedBy = $currentRevision?->authorId();
    }

    return Response::html($documentViewPage->render($document, $source, null, $requestPath, $lastEditedBy));
});

// GET/POST /wiki/{title}/edit — 문서 생성/편집 (태스크 0685, ACL 적용은
// 0687). DocumentEditorPage로 제목·본문·CSRF 토큰이 있는 폼을 렌더링한다.
// GET은 문서가 있으면 현재 리비전의 source로 미리 채우고, 없으면 빈 새
// 문서 폼으로 동작한다. POST는 CSRF 토큰을 검증하고(실패 시 403), 제목/
// 본문이 비어있으면 폼으로 되돌려 오류를 보여준다(422). 통과하면
// Document\Service로 문서를 생성/갱신하고 Revision\Repository로 새 리비전을
// 만든 뒤 문서의 currentRevisionId를 그 리비전으로 연결한다(0029
// create-first-revision과 동일한 순서). 저장에 성공하면 GET /wiki/{title}로
// 302 리다이렉트한다. documentRepository나 revisionRepository가 없으면(DB
// 미설정/오류) 폼으로 되돌아가 503을 반환해 죽지 않는다. 0687에서 GET/POST
// 모두 AclService로 현재 사용자(0686 세션)의 edit 권한을 확인한다 — 문서가
// 이미 있으면 그 문서의 규칙(없으면 네임스페이스 기본값)을, 새 문서면
// 네임스페이스 기본값을 사용한다. 거부되면 익명 사용자는 로그인 화면으로
// 유도(302 /login)하고, 로그인한 사용자는 PermissionDeniedPage로 403을
// 반환한다.
$router->register('GET', '/wiki/{title}/edit', static function (array $params) use (
    $documentRepository,
    $revisionRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter);
    $documentEditorPage = new DocumentEditorPage(null, $layout);
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

    $documentAcl = $document !== null ? $aclRuleRepository?->documentAcl($document->id()) : null;
    [$subjectType, $subjectId] = mintwiki_resolve_acl_subject($accountRepository, $sessionAdapter);
    $decision = $aclService->check(AclPermission::Edit, $subjectType, $subjectId, $documentAcl);

    if ($decision->isDenied()) {
        if ($subjectType === AclSubjectType::Anonymous) {
            return new Response(302, ['Location' => '/login']);
        }

        $permissionDeniedPage = new PermissionDeniedPage(null, $layout);

        return Response::html($permissionDeniedPage->render($decision), 403);
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

$router->register('POST', '/wiki/{title}/edit', static function (array $params) use (
    $documentRepository,
    $revisionRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter);
    $documentEditorPage = new DocumentEditorPage(null, $layout);
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

    $documentAcl = $existingDocument !== null ? $aclRuleRepository?->documentAcl($existingDocument->id()) : null;
    [$subjectType, $subjectId] = mintwiki_resolve_acl_subject($accountRepository, $sessionAdapter);
    $decision = $aclService->check(AclPermission::Edit, $subjectType, $subjectId, $documentAcl);

    if ($decision->isDenied()) {
        if ($subjectType === AclSubjectType::Anonymous) {
            return new Response(302, ['Location' => '/login']);
        }

        $permissionDeniedPage = new PermissionDeniedPage(null, $layout);

        return Response::html($permissionDeniedPage->render($decision), 403);
    }

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

// GET /admin — 관리자 콘솔 진입점 (태스크 0697). 0696 AdminAccessGate로
// 익명(302 /login)/비관리자(403)를 먼저 걸러내고, 관리자만 통과시켜
// AdminDashboardPage(Layout 재사용)를 렌더링해 관리 하위 화면(감사 로그,
// 신고, 사용자 차단, 유지보수, 백업/복원, 진단) 링크 목록을 보여준다.
// $accountRepository가 없으면(DB 미설정/오류) 세션에서 로그인 사용자를
// 복원할 수 없으므로 익명으로 간주해 /login으로 302한다 — 0674 계약과
// 동일한 판단이다.
$router->register('GET', '/admin', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter);

    if ($accountRepository === null) {
        return new Response(302, ['Location' => '/login']);
    }

    $sessionUserResolver = new SessionUserResolver($sessionAdapter, $accountRepository);
    $adminAccessGate = new AdminAccessGate($aclService, $sessionUserResolver, $layout);

    $gateResponse = $adminAccessGate->authorize();
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $adminDashboardPage = new AdminDashboardPage(null, $layout);

    return Response::html($adminDashboardPage->render());
});

// GET /admin/audit — 감사 로그 뷰어 (태스크 0698). 위 GET /admin과 동일하게
// 0696 AdminAccessGate로 익명(302 /login)/비관리자(403)를 먼저 걸러내고,
// 관리자만 통과시킨다. `$pdo`가 연결된 경우에만 RecentAuditEventsQuery로
// audit_event 테이블의 최근 이벤트(occurred_at 내림차순, 최대 100건)를 읽어
// AuditViewerPage(AuditRow 재사용)에 주입하고, 미설정/오류/조회 실패 시에는
// 빈 목록으로 대체해 AuditViewerPage가 빈 상태를 보여주게 한다 — 0674/0693과
// 동일한 판단이다.
$router->register('GET', '/admin/audit', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $pdo,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter);

    if ($accountRepository === null) {
        return new Response(302, ['Location' => '/login']);
    }

    $sessionUserResolver = new SessionUserResolver($sessionAdapter, $accountRepository);
    $adminAccessGate = new AdminAccessGate($aclService, $sessionUserResolver, $layout);

    $gateResponse = $adminAccessGate->authorize();
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $auditEvents = [];
    if ($pdo !== null) {
        try {
            $auditEvents = (new RecentAuditEventsQuery($pdo))->listRecentEvents();
        } catch (\Throwable $exception) {
            $auditEvents = [];
        }
    }

    $auditViewerPage = new AuditViewerPage(null, $layout);

    return Response::html($auditViewerPage->render($auditEvents));
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
    $errorPage = new ErrorPage(null, mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter));
    $html = $errorPage->renderNotFound($requestPath);
    $response = Response::html($html, 404);
}

mintwiki_send_response($response);
