<?php

declare(strict_types=1);

/**
 * MintWiki PHP 런타임의 프론트 컨트롤러 (태스크 0394, 0419, 0592, 0674, 0676, 0677, 0678, 0679, 0680, 0681, 0682, 0683, 0684, 0687, 0691, 0703, 0706, 0708).
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
 * 0699에서 `GET /admin/reports`(`AdminReportListPage`), `GET /admin/users/block`
 * (`BlockUserFormPage` 폼), `POST /admin/users/block`(`BlockUserHandler`)을
 * 등록했다 — 세 route 모두 동일한 0696 `AdminAccessGate`로 보호되고,
 * POST는 기존 `CsrfTokenService`로 CSRF 토큰을 검증한 뒤
 * `AccountRepository::block()`으로 대상 계정을 차단하고 폼으로 302
 * 리다이렉트한다. 0706에서 `GET /wiki/{title}`의 `DocumentViewPage` 렌더러를
 * `PlainTextDocumentRenderer`(기본값)에서 `MintWiki\Render\NamuMarkDocumentRenderer`로
 * 교체했다 — 0704/0705 인라인/블록 파서를 실제로 호출해 저장된 위키 문법
 * ('''굵게'''/[[링크]]/표/제목 등)을 HTML(+ 제목 2개 이상이면 목차)로
 * 렌더링한다. 0708에서 `POST /wiki/{title}/preview`를 등록했다 — 편집 폼과
 * 같은 title/source/summary/csrf_token을 받아 저장 없이 위 `$documentRenderer`
 * (0706과 공유하는 같은 `NamuMarkDocumentRenderer` 인스턴스)로 렌더링한
 * 결과를 `DocumentEditorPage`의 미리보기 영역에 채운 편집 화면으로 돌려준다.
 * ACL(익명 정책 포함)/CSRF 검증은 `POST /wiki/{title}/edit`과 동일한 로직을
 * 그대로 따른다. JS 없이도 "미리보기" 버튼의 `formaction`으로 이 route에
 * 도달해 페이지 전체가 다시 그려지고(원문 유지), `assets/js/edit-preview.js`가
 * 있으면 fetch로 그 이동을 가로채 미리보기 영역만 갱신한다(CSRF 토큰도 응답의
 * 새 값으로 교체). 0710에서 `GET /wiki/{title}/history`와
 * `GET /wiki/{title}/diff?from={revId}&to={revId}`를 등록해 액션 탭(0692)의
 * "역사" 링크가 실제로 동작하게 했다 — 둘 다 `GET /wiki/{title}`과 동일한
 * ACL read 검사를 거친다(거부되면 `PermissionDeniedPage`로 403). history는
 * `$revisionRepository->listByDocumentId()`가 반환하는(생성 순서, 오름차순)
 * 목록을 뒤집어 시간 내림차순으로 `DocumentHistoryPage`에 넘긴다 — 리비전이
 * 없거나 1개뿐이면 그 page가 알아서 빈 상태/단일 상태를 안전하게 그린다.
 * diff는 쿼리 문자열의 `from`/`to` id로 `$revisionRepository->get()`을 두 번
 * 호출해 두 리비전을 찾고, 하나라도 없거나 문서가 다르면(다른 문서의
 * 리비전 id를 섞어 넣는 시도 포함) `ErrorPage`로 404를 반환한다. 문서 자체가
 * 없거나 `$documentRepository === null`(DB 미설정/오류)인 경우도 동일하게
 * 404로 처리한다. 리비전 비교는 `DocumentDiffPage`가 두 source를 줄 단위
 * LCS diff로 비교해 보여준다(렌더 결과가 아닌 원문 기준 diff, out of scope인
 * 되돌리기는 다루지 않는다). 0712에서 `GET`/`POST /wiki/{title}/discussion`과
 * `POST /wiki/{title}/discussion/{threadId}/comment`를 등록해 액션 탭의
 * "토론" 링크가 실제로 동작하게 했다 — 0711 `Discussion\PdoRepository`/
 * `Discussion\Service`로 문서의 스레드·댓글을 읽고 쓴다. GET은 위 history/diff
 * route와 동일한 ACL read 검사를 거치고(거부되면 403), 그와 별개로
 * `Permission::Discuss` 검사 결과를 `DiscussionPage`에 넘겨 새 스레드/댓글
 * form을 보여줄지(허용) 로그인 안내로 대체할지(거부) 정한다. 두 POST route도
 * discuss 권한을 검사해 거부되면 위 edit route와 같은 관례로 익명은
 * `/login`으로 302, 로그인한 사용자는 `PermissionDeniedPage`로 403을
 * 반환한다. CSRF 검증 실패는 403으로, 제목/본문이 비어있으면(Thread/Comment
 * 생성자의 `Empty*Error`) 422로 폼에 오류를 담아 되돌리며, 성공하면
 * `GET /wiki/{title}/discussion`으로 302 리다이렉트한다. 댓글 POST는 URL의
 * threadId가 그 문서 소속 스레드가 아니면(또는 없으면) 404를 반환한다. 나머지
 * route(`docs/php-db-ui-micro-job-prompts-0351-0670.md`)는 이후 태스크에서
 * 이어진다.
 */

$autoloadPath = __DIR__ . '/../vendor/autoload.php';
if (!is_file($autoloadPath) && is_file(__DIR__ . '/vendor/autoload.php')) {
    $autoloadPath = __DIR__ . '/vendor/autoload.php';
}
require $autoloadPath;

use MintWiki\Acl\AclService;
use MintWiki\Acl\DefaultPolicy;
use MintWiki\Acl\NamespaceAclDefaults;
use MintWiki\Acl\PdoRepository as AclPdoRepository;
use MintWiki\Acl\Permission as AclPermission;
use MintWiki\Acl\SubjectType as AclSubjectType;
use MintWiki\Admin\FileBackupRunner;
use MintWiki\App\AppBootstrap;
use MintWiki\App\ConfigLoader;
use MintWiki\App\LocalConfigLoader;
use MintWiki\App\MaintenanceModeStateStore;
use MintWiki\App\StoragePathConfig;
use MintWiki\Audit\RecentAuditEventsQuery;
use MintWiki\Discussion\EmptyCommentBodyError;
use MintWiki\Discussion\EmptyCommentCreatedByError;
use MintWiki\Discussion\EmptyThreadCreatedByError;
use MintWiki\Discussion\EmptyThreadTitleError;
use MintWiki\Discussion\PdoRepository as DiscussionPdoRepository;
use MintWiki\Discussion\Service as DiscussionService;
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
use MintWiki\Render\NamuMarkDocumentRenderer;
use MintWiki\Revision\PdoRepository as RevisionPdoRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\AdminAccessGate;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\LoginHandler;
use MintWiki\Security\LogoutHandler;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\AdminDashboardPage;
use MintWiki\Ui\AdminReportListPage;
use MintWiki\Ui\AuditViewerPage;
use MintWiki\Ui\BackupPage;
use MintWiki\Ui\BlockUserFormPage;
use MintWiki\Ui\DiscussionPage;
use MintWiki\Ui\DocumentDiffPage;
use MintWiki\Ui\DocumentEditorPage;
use MintWiki\Ui\DocumentHistoryPage;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\FilePermissionDiagnosticsPage;
use MintWiki\Ui\FrontPage;
use MintWiki\Ui\InstallAdminAccountFormPage;
use MintWiki\Ui\InstallDBFormPage;
use MintWiki\Ui\InstallRequiredPage;
use MintWiki\Ui\InstallSchemaApplyPage;
use MintWiki\Ui\InstallWelcomePage;
use MintWiki\Ui\Layout;
use MintWiki\Ui\LoginPage;
use MintWiki\Ui\MaintenanceModePage;
use MintWiki\Ui\Navigation;
use MintWiki\Ui\NavigationBar;
use MintWiki\Ui\NavigationItem;
use MintWiki\Ui\OperationalDiagnosticsPage;
use MintWiki\Ui\PermissionDeniedPage;
use MintWiki\Ui\RestorePage;
use MintWiki\User\AccountRepository;
use MintWiki\User\BlockUserHandler;

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
 * Layout을 만든다 (태스크 0691). 0703에서 배포 화면의 새 문서 작성 진입점으로
 * "글쓰기" 링크를 기본 메뉴에 추가했다. NavigationBar는 $accountRepository가
 * 없거나(DB 미설정/오류) 세션에 로그인 사용자가 없으면 자동으로 로그아웃 상태로
 * 렌더링한다.
 */
function mintwiki_build_layout(
    string $requestPath,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    ?AclService $aclService = null
): Layout
{
    $currentUser = $accountRepository !== null
        ? (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve()
        : null;

    $navigationItems = [
        new NavigationItem('/write', '글쓰기', '/write'),
    ];
    if ($currentUser !== null && $aclService !== null) {
        $adminDecision = $aclService->check(AclPermission::Admin, AclSubjectType::User, $currentUser->id());
        if ($adminDecision->isAllowed()) {
            $navigationItems[] = new NavigationItem('/admin', '관리', '/admin');
        }
    }

    $navigation = new Navigation($navigationItems);
    $headerContent = (new NavigationBar())->render($navigation, $requestPath, [], $currentUser);

    return new Layout(null, $headerContent);
}

function mintwiki_authorize_admin_route(
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    AclService $aclService,
    Layout $layout
): ?Response {
    if ($accountRepository === null) {
        return new Response(302, ['Location' => '/login']);
    }

    $sessionUserResolver = new SessionUserResolver($sessionAdapter, $accountRepository);
    $adminAccessGate = new AdminAccessGate($aclService, $sessionUserResolver, $layout);

    return $adminAccessGate->authorize();
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

/**
 * 편집 요약 입력값을 정규화한다 (태스크 0707).
 *
 * 앞뒤 공백을 제거하고, 비어 있으면 기본 문자열로 대체해 리비전에는 항상
 * 사람이 읽을 수 있는 요약이 남게 한다. 길이 제한(500자)은 저장 전
 * 검증 단계에서 별도로 걸러내므로 여기서는 자르지 않는다.
 */
function mintwiki_normalize_edit_summary(string $summaryInput): string
{
    $trimmed = trim($summaryInput);

    return $trimmed === '' ? '편집 요약 없음' : $trimmed;
}

/**
 * 문서의 토론 스레드/댓글 목록을 조회한다 (태스크 0712). `$pdo`가 없으면(DB
 * 미설정/오류) 빈 목록을 반환해 `DiscussionPage`가 빈 상태를 안전하게
 * 그리게 한다.
 *
 * @return array{0: array<int, \MintWiki\Discussion\Thread>, 1: array<string, array<int, \MintWiki\Discussion\Comment>>}
 */
function mintwiki_load_discussion_data(?PDO $pdo, string $documentId): array
{
    if ($pdo === null) {
        return [[], []];
    }

    $discussionService = new DiscussionService(new DiscussionPdoRepository($pdo));
    $threads = $discussionService->listThreadsByDocumentId($documentId);

    $commentsByThreadId = [];
    foreach ($threads as $thread) {
        $commentsByThreadId[$thread->id()] = $discussionService->listCommentsByThreadId($thread->id());
    }

    return [$threads, $commentsByThreadId];
}

/**
 * 새 스레드/댓글의 작성자로 기록할 식별자를 정한다 (태스크 0712). 로그인한
 * 사용자가 있으면 그 username을, 없으면(익명 쓰기가 acl_rule로 명시적으로
 * 허용된 드문 경우) 'anonymous'를 대체값으로 쓴다 — Thread/Comment
 * 생성자는 빈 문자열 createdBy를 거부하므로 항상 채워진 값이 필요하다.
 */
function mintwiki_resolve_discussion_created_by(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): string
{
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return $currentUser->username();
        }
    }

    return 'anonymous';
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

// ACL (태스크 0687). 문서별 규칙(acl_rule)이 있으면 AclService가 그것만
// 쓰고, 없으면 네임스페이스 기본 규칙(acl_namespace_rule)으로 대체한다.
// 0702에서 상단바의 관리자 전용 "관리" 링크도 이 서비스로 판정하므로
// route 등록보다 먼저 구성한다.
$aclRuleRepository = $pdo !== null ? new AclPdoRepository($pdo) : null;
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
if ($aclRuleRepository !== null) {
    try {
        $dbNamespaceRules = $aclRuleRepository->namespaceRules(NamespaceAclDefaults::DEFAULT_NAMESPACE);
        if ($dbNamespaceRules !== []) {
            $namespaceAclDefaults->register(
                NamespaceAclDefaults::DEFAULT_NAMESPACE,
                array_merge($dbNamespaceRules, DefaultPolicy::defaultRules())
            );
        }
    } catch (\Throwable $exception) {
        // schema 미적용 상태 — DefaultPolicy로 계속 진행한다.
    }
}
$aclService = new AclService($namespaceAclDefaults);

$maintenanceModeStateStore = MaintenanceModeStateStore::atDefaultPath();
if (
    $maintenanceModeStateStore->isEnabled()
    && !$isApiRequest
    && $requestPath !== '/login'
    && $requestPath !== '/health'
    && !str_starts_with($requestPath, '/admin')
) {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    mintwiki_send_response(Response::html((new MaintenanceModePage(null, $layout))->render(), 503));

    return;
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

// GET / — 나무위키식 대문(프론트페이지) (태스크 0526, 상단 네비게이션 바
// 연결은 0691, 대문 개편은 0693). FrontPage(검색 영역 + 최근 편집된 문서
// 목록 + 사이트 소개)를 Layout(0691 스킨) 위에 렌더링한다. 최근 문서
// 목록은 DB가 연결된 경우에만 RecentDocumentsQuery로 조회하고, 미설정/
// 오류 상태(schema 미적용 포함)에서는 빈 목록으로 대체해 FrontPage가
// 안전하게 빈 상태 안내를 보여주게 한다 — 0674 계약(GET /가 죽지 않음)과
// 동일한 판단이다.
$router->register('GET', '/', static function () use ($accountRepository, $sessionAdapter, $pdo, $aclService): Response {
    $layout = mintwiki_build_layout('/', $accountRepository, $sessionAdapter, $aclService);
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

// 문서 view(GET /wiki/{title})와 편집 미리보기(POST /wiki/{title}/preview,
// 태스크 0708)가 같은 렌더러 인스턴스를 공유한다 — 두 화면의 렌더링
// 결과가 갈라지지 않는다는 것을 보장한다.
$documentRenderer = new NamuMarkDocumentRenderer();

$configLoader = new ConfigLoader((new LocalConfigLoader())->load());
$storagePathConfig = new StoragePathConfig($configLoader);
$backupRunner = new FileBackupRunner($storagePathConfig->rootPath() . '/backups');

// GET/POST /login, GET/POST /logout (태스크 0686). $accountRepository/
// $sessionAdapter는 위에서(태스크 0691) 앞당겨 정의했다 — 로그인 상태
// 확인/자격 증명 대조에 그대로 쓴다.

$router->register('GET', '/login', static function () use ($accountRepository, $sessionAdapter, $aclService): Response {
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return new Response(302, ['Location' => '/']);
        }
    }

    $layout = mintwiki_build_layout('/login', $accountRepository, $sessionAdapter, $aclService);
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

// GET /write — 새 문서 작성 진입점 (태스크 0703). 실제 저장은 0685에서
// 검증된 `/wiki/{title}/edit` POST 흐름을 재사용한다. 제목을 아직 모르는
// 상태이므로 sentinel title로 form action만 만들고, POST 핸들러가 사용자가
// 입력한 title/source를 기준으로 새 문서를 생성한다. 익명 사용자는 기존 edit
// ACL 경로에서 `/login`으로 유도된다.
$router->register('GET', '/write', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $documentEditorPage = new DocumentEditorPage(null, $layout);

    return Response::html($documentEditorPage->render('__new__', '', '', true));
});

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
    $requestPath,
    $documentRenderer
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $documentViewPage = new DocumentViewPage(null, $layout, $documentRenderer);
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
// 0687, 편집 요약 필드는 0707). DocumentEditorPage로 제목·본문·편집 요약·
// CSRF 토큰이 있는 폼을 렌더링한다.
// GET은 문서가 있으면 현재 리비전의 source로 미리 채우고, 없으면 빈 새
// 문서 폼으로 동작한다(편집 요약은 리비전마다 새로 입력하므로 항상 빈 값).
// POST는 CSRF 토큰을 검증하고(실패 시 403), 제목/본문이 비어있거나 편집
// 요약이 500자를 넘으면 폼으로 되돌려 오류를 보여준다(422). 편집 요약이
// 비어 있으면 mintwiki_normalize_edit_summary()가 기본 문자열로 대체한다.
// 통과하면
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
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
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
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $documentEditorPage = new DocumentEditorPage(null, $layout);
    $csrfTokenService = new CsrfTokenService();
    $requestedTitle = rawurldecode($params['title'] ?? '');

    $titleInput = is_string($_POST['title'] ?? null) ? $_POST['title'] : '';
    $sourceInput = is_string($_POST['source'] ?? null) ? $_POST['source'] : '';
    $summaryInput = is_string($_POST['summary'] ?? null) ? $_POST['summary'] : '';
    $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

    if ($documentRepository === null || $revisionRepository === null) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, true, [
                '_form' => '데이터베이스가 설정되지 않아 저장할 수 없습니다.',
            ], $summaryInput),
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
            ], $summaryInput),
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
    if (mb_strlen(trim($summaryInput)) > 500) {
        $validationErrors['summary'] = '편집 요약은 500자 이하로 입력하세요.';
    }

    if ($validationErrors !== []) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, $validationErrors, $summaryInput),
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
            mintwiki_normalize_edit_summary($summaryInput),
            $parentRevisionId
        ));

        $document = $documentService->update(new Document($document->id(), $document->title(), $revision->id()));
    } catch (EmptyTitleError) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                'title' => '제목을 입력하세요.',
            ], $summaryInput),
            422
        );
    } catch (DuplicateNormalizedTitleError) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                'title' => '이미 존재하는 제목입니다.',
            ], $summaryInput),
            409
        );
    }

    return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title())]);
});

// POST /wiki/{title}/preview — 편집 화면 저장 전 미리보기 (태스크 0708).
// title/source/summary/csrf_token은 편집 폼과 동일하게 받되 아무것도
// 저장하지 않는다. ACL 검사(익명 정책 포함)와 CSRF 검증은 위 POST
// /wiki/{title}/edit와 동일한 로직을 그대로 따른다 — DB 미설정
// (documentRepository === null) 상태에서는 편집 GET과 마찬가지로 ACL 검사
// 자체를 건너뛴다(저장할 대상이 없으므로). 통과하면 위에서 만든
// $documentRenderer(0706 NamuMarkDocumentRenderer, GET /wiki/{title} 뷰와
// 공유)로 source를 렌더링해 DocumentEditorPage의 미리보기 영역에 채운 편집
// 화면을 그대로 돌려준다 — 입력했던 title/source/summary는 그대로
// 유지되고(원문 유지), CSRF 토큰은 새로 발급되어(0540 CsrfTokenService는
// 검증한 토큰을 소모한다) 이어지는 미리보기/저장 제출에 계속 쓸 수 있다.
$router->register('POST', '/wiki/{title}/preview', static function (array $params) use (
    $documentRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath,
    $documentRenderer
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $documentEditorPage = new DocumentEditorPage(null, $layout);
    $csrfTokenService = new CsrfTokenService();
    $requestedTitle = rawurldecode($params['title'] ?? '');

    $titleInput = is_string($_POST['title'] ?? null) ? $_POST['title'] : '';
    $sourceInput = is_string($_POST['source'] ?? null) ? $_POST['source'] : '';
    $summaryInput = is_string($_POST['summary'] ?? null) ? $_POST['summary'] : '';
    $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

    $isNew = true;
    if ($documentRepository !== null) {
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
    }

    if (!$csrfTokenService->validate($csrfToken)) {
        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [
                '_form' => '유효하지 않은 요청입니다. 다시 시도하세요.',
            ], $summaryInput),
            403
        );
    }

    $previewHtml = '<p>미리볼 내용이 없습니다.</p>';
    if (trim($sourceInput) !== '') {
        try {
            $previewHtml = $documentRenderer->render($sourceInput)->html();
        } catch (\Throwable) {
            $previewHtml = '<p>미리보기 렌더링에 실패했습니다.</p>';
        }
    }

    return Response::html(
        $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [], $summaryInput, $previewHtml)
    );
});

// GET /wiki/{title}/history — 문서 히스토리 (태스크 0710). ACL read 검사는
// GET /wiki/{title}과 동일한 로직을 그대로 따른다(문서별 규칙 -> 없으면
// 네임스페이스 기본값). revisionRepository->listByDocumentId()는 생성
// 순서(오름차순)로 반환하므로 array_reverse()로 뒤집어 시간 내림차순으로
// DocumentHistoryPage에 넘긴다 — 그 page가 빈/단일 리비전 상태를 안전하게
// 그린다. documentRepository가 없거나(DB 미설정/오류) 문서를 찾을 수 없으면
// ErrorPage로 404를 반환한다.
$router->register('GET', '/wiki/{title}/history', static function (array $params) use (
    $documentRepository,
    $revisionRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $requestedTitle = rawurldecode($params['title'] ?? '');

    if ($documentRepository === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentAcl = $aclRuleRepository?->documentAcl($document->id());
    [$subjectType, $subjectId] = mintwiki_resolve_acl_subject($accountRepository, $sessionAdapter);
    $decision = $aclService->check(AclPermission::Read, $subjectType, $subjectId, $documentAcl);

    if ($decision->isDenied()) {
        $permissionDeniedPage = new PermissionDeniedPage(null, $layout);

        return Response::html($permissionDeniedPage->render($decision), 403);
    }

    $revisions = $revisionRepository !== null
        ? array_reverse($revisionRepository->listByDocumentId($document->id()))
        : [];

    $documentHistoryPage = new DocumentHistoryPage(null, $layout);

    return Response::html($documentHistoryPage->render($document, $revisions));
});

// GET /wiki/{title}/diff?from={revId}&to={revId} — 리비전 간 diff (태스크
// 0710). ACL read 검사는 위 history route와 동일하다. 쿼리 문자열의
// from/to id로 revisionRepository->get()을 각각 호출해 두 리비전을 찾고,
// 하나라도 없거나 이 문서의 리비전이 아니면(다른 문서 리비전 id를 섞어
// 넣는 시도 포함) ErrorPage로 404를 반환한다. 통과하면 DocumentDiffPage가
// 두 리비전 source를 줄 단위로 비교해 보여준다.
$router->register('GET', '/wiki/{title}/diff', static function (array $params) use (
    $documentRepository,
    $revisionRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $requestedTitle = rawurldecode($params['title'] ?? '');

    if ($documentRepository === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentAcl = $aclRuleRepository?->documentAcl($document->id());
    [$subjectType, $subjectId] = mintwiki_resolve_acl_subject($accountRepository, $sessionAdapter);
    $decision = $aclService->check(AclPermission::Read, $subjectType, $subjectId, $documentAcl);

    if ($decision->isDenied()) {
        $permissionDeniedPage = new PermissionDeniedPage(null, $layout);

        return Response::html($permissionDeniedPage->render($decision), 403);
    }

    $fromId = is_string($_GET['from'] ?? null) ? $_GET['from'] : '';
    $toId = is_string($_GET['to'] ?? null) ? $_GET['to'] : '';

    $fromRevision = ($revisionRepository !== null && $fromId !== '') ? $revisionRepository->get($fromId) : null;
    $toRevision = ($revisionRepository !== null && $toId !== '') ? $revisionRepository->get($toId) : null;

    if (
        $fromRevision === null
        || $toRevision === null
        || $fromRevision->documentId() !== $document->id()
        || $toRevision->documentId() !== $document->id()
    ) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentDiffPage = new DocumentDiffPage(null, $layout);

    return Response::html($documentDiffPage->render($document, $fromRevision, $toRevision));
});

// GET /wiki/{title}/discussion, POST /wiki/{title}/discussion(새 스레드),
// POST /wiki/{title}/discussion/{threadId}/comment(댓글 추가) — 문서별 토론
// (태스크 0712). 0711이 만든 `Discussion\PdoRepository`/`Discussion\Service`로
// 실제 스레드/댓글을 읽고 쓴다. GET은 위 history/diff route와 동일하게 read
// 권한을 확인한다(거부되면 PermissionDeniedPage로 403). 그와 별개로 discuss
// 권한을 확인해 그 결과(`$discussDecision->isAllowed()`)를 DiscussionPage에
// 넘긴다 — 거부되면(로그인하지 않았거나 acl_rule로 명시적으로 막힌 경우) 새
// 스레드/댓글 form 대신 로그인 안내를 보여준다. 두 POST route는 문서를 찾을
// 수 없으면 404, discuss 권한이 없으면 위 edit route와 동일한 관례로
// 익명은 /login으로 302, 로그인한 사용자는 403(PermissionDeniedPage)을
// 반환한다. CSRF 토큰 검증에 실패하면 403으로 폼을 다시 보여주고, 제목/본문이
// 비어있으면(Thread/Comment 생성자가 `Empty*Error`를 던진다) 422로 오류를
// 담아 되돌린다. 저장에 성공하면 `GET /wiki/{title}/discussion`으로 302
// 리다이렉트한다. 댓글 POST는 URL의 threadId가 이 문서 소속 스레드가 아니면
// (또는 존재하지 않으면) 404를 반환한다.
$router->register('GET', '/wiki/{title}/discussion', static function (array $params) use (
    $documentRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath,
    $pdo
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $requestedTitle = rawurldecode($params['title'] ?? '');

    if ($documentRepository === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentAcl = $aclRuleRepository?->documentAcl($document->id());
    [$subjectType, $subjectId] = mintwiki_resolve_acl_subject($accountRepository, $sessionAdapter);
    $readDecision = $aclService->check(AclPermission::Read, $subjectType, $subjectId, $documentAcl);

    if ($readDecision->isDenied()) {
        $permissionDeniedPage = new PermissionDeniedPage(null, $layout);

        return Response::html($permissionDeniedPage->render($readDecision), 403);
    }

    $discussDecision = $aclService->check(AclPermission::Discuss, $subjectType, $subjectId, $documentAcl);

    [$threads, $commentsByThreadId] = mintwiki_load_discussion_data($pdo, $document->id());

    $discussionPage = new DiscussionPage(null, $layout);

    return Response::html(
        $discussionPage->render($document, $threads, $commentsByThreadId, [], [], $discussDecision->isAllowed())
    );
});

$router->register('POST', '/wiki/{title}/discussion', static function (array $params) use (
    $documentRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath,
    $pdo
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $requestedTitle = rawurldecode($params['title'] ?? '');
    $csrfTokenService = new CsrfTokenService();

    $titleInput = is_string($_POST['title'] ?? null) ? $_POST['title'] : '';
    $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

    if ($documentRepository === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentAcl = $aclRuleRepository?->documentAcl($document->id());
    [$subjectType, $subjectId] = mintwiki_resolve_acl_subject($accountRepository, $sessionAdapter);
    $decision = $aclService->check(AclPermission::Discuss, $subjectType, $subjectId, $documentAcl);

    if ($decision->isDenied()) {
        if ($subjectType === AclSubjectType::Anonymous) {
            return new Response(302, ['Location' => '/login']);
        }

        $permissionDeniedPage = new PermissionDeniedPage(null, $layout);

        return Response::html($permissionDeniedPage->render($decision), 403);
    }

    [$threads, $commentsByThreadId] = mintwiki_load_discussion_data($pdo, $document->id());
    $discussionPage = new DiscussionPage(null, $layout);

    if (!$csrfTokenService->validate($csrfToken)) {
        return Response::html(
            $discussionPage->render($document, $threads, $commentsByThreadId, [
                '_form' => '유효하지 않은 요청입니다. 다시 시도하세요.',
            ], [], true),
            403
        );
    }

    $discussionService = new DiscussionService(new DiscussionPdoRepository($pdo));
    $createdBy = mintwiki_resolve_discussion_created_by($accountRepository, $sessionAdapter);

    try {
        $discussionService->createThread($document->id(), $titleInput, $createdBy);
    } catch (EmptyThreadTitleError) {
        return Response::html(
            $discussionPage->render($document, $threads, $commentsByThreadId, [
                'title' => '스레드 제목을 입력하세요.',
            ], [], true),
            422
        );
    } catch (EmptyThreadCreatedByError) {
        return new Response(302, ['Location' => '/login']);
    }

    return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title()) . '/discussion']);
});

$router->register('POST', '/wiki/{title}/discussion/{threadId}/comment', static function (array $params) use (
    $documentRepository,
    $aclRuleRepository,
    $aclService,
    $accountRepository,
    $sessionAdapter,
    $requestPath,
    $pdo
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $requestedTitle = rawurldecode($params['title'] ?? '');
    $threadId = $params['threadId'] ?? '';
    $csrfTokenService = new CsrfTokenService();

    $bodyInput = is_string($_POST['body'] ?? null) ? $_POST['body'] : '';
    $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

    if ($documentRepository === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentService = new DocumentService($documentRepository);

    try {
        $document = $documentService->getByTitle($requestedTitle);
    } catch (EmptyTitleError) {
        $document = null;
    }

    if ($document === null) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    $documentAcl = $aclRuleRepository?->documentAcl($document->id());
    [$subjectType, $subjectId] = mintwiki_resolve_acl_subject($accountRepository, $sessionAdapter);
    $decision = $aclService->check(AclPermission::Discuss, $subjectType, $subjectId, $documentAcl);

    if ($decision->isDenied()) {
        if ($subjectType === AclSubjectType::Anonymous) {
            return new Response(302, ['Location' => '/login']);
        }

        $permissionDeniedPage = new PermissionDeniedPage(null, $layout);

        return Response::html($permissionDeniedPage->render($decision), 403);
    }

    $discussionService = new DiscussionService(new DiscussionPdoRepository($pdo));
    $thread = $discussionService->getThread($threadId);

    if ($thread === null || $thread->documentId() !== $document->id()) {
        return Response::html((new ErrorPage(null, $layout))->renderNotFound($requestPath), 404);
    }

    [$threads, $commentsByThreadId] = mintwiki_load_discussion_data($pdo, $document->id());
    $discussionPage = new DiscussionPage(null, $layout);

    if (!$csrfTokenService->validate($csrfToken)) {
        return Response::html(
            $discussionPage->render($document, $threads, $commentsByThreadId, [], [
                $threadId => ['_form' => '유효하지 않은 요청입니다. 다시 시도하세요.'],
            ], true),
            403
        );
    }

    $createdBy = mintwiki_resolve_discussion_created_by($accountRepository, $sessionAdapter);

    try {
        $discussionService->addComment($threadId, $bodyInput, $createdBy);
    } catch (EmptyCommentBodyError) {
        return Response::html(
            $discussionPage->render($document, $threads, $commentsByThreadId, [], [
                $threadId => ['body' => '댓글 본문을 입력하세요.'],
            ], true),
            422
        );
    } catch (EmptyCommentCreatedByError) {
        return new Response(302, ['Location' => '/login']);
    }

    return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title()) . '/discussion']);
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
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);

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
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);

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

// GET /admin/reports — 신고 목록 (태스크 0699). 위 GET /admin/audit과 동일하게
// 0696 AdminAccessGate로 익명(302 /login)/비관리자(403)를 먼저 걸러내고
// 관리자만 AdminReportListPage(Layout 재사용)를 렌더링한다. 신고 접수(사용자측)
// 흐름과 실데이터 연동은 이 태스크의 범위 밖이라 빈 상태만 보여준다.
$router->register('GET', '/admin/reports', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);

    if ($accountRepository === null) {
        return new Response(302, ['Location' => '/login']);
    }

    $sessionUserResolver = new SessionUserResolver($sessionAdapter, $accountRepository);
    $adminAccessGate = new AdminAccessGate($aclService, $sessionUserResolver, $layout);

    $gateResponse = $adminAccessGate->authorize();
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $adminReportListPage = new AdminReportListPage(null, $layout);

    return Response::html($adminReportListPage->render());
});

// GET /admin/users/block — 사용자 차단 form (태스크 0699). 동일한 게이트를
// 적용한 뒤 BlockUserFormPage(CSRF 토큰 포함)를 렌더링한다.
$router->register('GET', '/admin/users/block', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);

    if ($accountRepository === null) {
        return new Response(302, ['Location' => '/login']);
    }

    $sessionUserResolver = new SessionUserResolver($sessionAdapter, $accountRepository);
    $adminAccessGate = new AdminAccessGate($aclService, $sessionUserResolver, $layout);

    $gateResponse = $adminAccessGate->authorize();
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $blockUserFormPage = new BlockUserFormPage(null, $layout);

    return Response::html($blockUserFormPage->render());
});

// POST /admin/users/block — 사용자 차단 처리 (태스크 0699). 위와 동일한
// 게이트를 통과한 뒤 BlockUserHandler(CSRF 검증 + AccountRepository::block())로
// 제출을 처리한다. $accountRepository가 없으면(DB 미설정) 게이트가 이미
// /login으로 302하므로 이 지점에는 DB가 항상 연결되어 있다.
$router->register('POST', '/admin/users/block', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);

    if ($accountRepository === null) {
        return new Response(302, ['Location' => '/login']);
    }

    $sessionUserResolver = new SessionUserResolver($sessionAdapter, $accountRepository);
    $adminAccessGate = new AdminAccessGate($aclService, $sessionUserResolver, $layout);

    $gateResponse = $adminAccessGate->authorize();
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $blockUserFormPage = new BlockUserFormPage(null, $layout);
    $blockUserHandler = new BlockUserHandler($accountRepository, new CsrfTokenService(), $blockUserFormPage);

    return $blockUserHandler->handle($_POST);
});

// GET/POST /admin/maintenance — 유지보수 모드 관리 (태스크 0700).
$router->register('GET', '/admin/maintenance', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $maintenanceModeStateStore,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $gateResponse = mintwiki_authorize_admin_route($accountRepository, $sessionAdapter, $aclService, $layout);
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $page = new MaintenanceModePage(null, $layout);

    return Response::html($page->renderAdmin($maintenanceModeStateStore->isEnabled()));
});

$router->register('POST', '/admin/maintenance', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $maintenanceModeStateStore,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $gateResponse = mintwiki_authorize_admin_route($accountRepository, $sessionAdapter, $aclService, $layout);
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $page = new MaintenanceModePage(null, $layout);
    $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';
    if (!(new CsrfTokenService())->validate($csrfToken)) {
        return Response::html($page->renderAdmin($maintenanceModeStateStore->isEnabled(), [
            '_form' => '유효하지 않은 요청입니다. 다시 시도하세요.',
        ]), 403);
    }

    try {
        $maintenanceModeStateStore->setEnabled(($_POST['enabled'] ?? null) === '1');
    } catch (\RuntimeException $exception) {
        return Response::html($page->renderAdmin($maintenanceModeStateStore->isEnabled(), [
            '_form' => $exception->getMessage(),
        ]), 500);
    }

    return new Response(302, ['Location' => '/admin/maintenance']);
});

// GET/POST /admin/backup — 백업 생성/목록 (태스크 0701).
$router->register('GET', '/admin/backup', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $backupRunner,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $gateResponse = mintwiki_authorize_admin_route($accountRepository, $sessionAdapter, $aclService, $layout);
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $page = new BackupPage(null, $layout);

    return Response::html($page->render($backupRunner->listBackups()));
});

$router->register('POST', '/admin/backup', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $backupRunner,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $gateResponse = mintwiki_authorize_admin_route($accountRepository, $sessionAdapter, $aclService, $layout);
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $page = new BackupPage(null, $layout);
    $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';
    if (!(new CsrfTokenService())->validate($csrfToken)) {
        return Response::html($page->render($backupRunner->listBackups(), null, [
            '_form' => '유효하지 않은 요청입니다. 다시 시도하세요.',
        ]), 403);
    }

    try {
        $backupName = $backupRunner->createBackup();
    } catch (\RuntimeException $exception) {
        return Response::html($page->render($backupRunner->listBackups(), null, [
            '_form' => $exception->getMessage(),
        ]), 500);
    }

    return Response::html($page->render($backupRunner->listBackups(), '백업을 생성했습니다: ' . $backupName));
});

// GET/POST /admin/restore — 복원 파일 접수 (태스크 0701).
$router->register('GET', '/admin/restore', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $gateResponse = mintwiki_authorize_admin_route($accountRepository, $sessionAdapter, $aclService, $layout);
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    return Response::html((new RestorePage(null, $layout))->render());
});

$router->register('POST', '/admin/restore', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $backupRunner,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $gateResponse = mintwiki_authorize_admin_route($accountRepository, $sessionAdapter, $aclService, $layout);
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    $page = new RestorePage(null, $layout);
    $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';
    if (!(new CsrfTokenService())->validate($csrfToken)) {
        return Response::html($page->render([
            '_form' => '유효하지 않은 요청입니다. 다시 시도하세요.',
        ]), 403);
    }
    if (($_POST['confirm_restore'] ?? null) !== '1') {
        return Response::html($page->render([
            'confirm_restore' => '복원을 실행하려면 위험 작업 확인에 동의해야 합니다.',
        ]), 422);
    }

    try {
        $backupRunner->restoreBackup(is_array($_FILES['backup_file'] ?? null) ? $_FILES['backup_file'] : []);
    } catch (\RuntimeException $exception) {
        return Response::html($page->render([
            'backup_file' => $exception->getMessage(),
        ]), 422);
    }

    return new Response(302, ['Location' => '/admin/backup']);
});

// GET /admin/diagnostics, /admin/diagnostics/files — 운영 진단 (태스크 0702).
$router->register('GET', '/admin/diagnostics', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $gateResponse = mintwiki_authorize_admin_route($accountRepository, $sessionAdapter, $aclService, $layout);
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    return Response::html((new OperationalDiagnosticsPage(null, $layout))->render());
});

$router->register('GET', '/admin/diagnostics/files', static function () use (
    $accountRepository,
    $sessionAdapter,
    $aclService,
    $requestPath
): Response {
    $layout = mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService);
    $gateResponse = mintwiki_authorize_admin_route($accountRepository, $sessionAdapter, $aclService, $layout);
    if ($gateResponse !== null) {
        return $gateResponse;
    }

    return Response::html((new FilePermissionDiagnosticsPage(null, $layout))->render());
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
    $errorPage = new ErrorPage(null, mintwiki_build_layout($requestPath, $accountRepository, $sessionAdapter, $aclService));
    $html = $errorPage->renderNotFound($requestPath);
    $response = Response::html($html, 404);
}

mintwiki_send_response($response);
