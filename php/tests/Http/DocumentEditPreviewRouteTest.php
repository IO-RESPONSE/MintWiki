<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0708에서 등록하는 `POST /wiki/{title}/preview`와
 * `DocumentEditorPage`의 미리보기 영역을 확인하는 smoke test. phpunit 없이
 * `php` CLI만으로 실행된다(0685 `DocumentEditRouteTest.php`와 동일한 방식) —
 * index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록 로직(ACL/CSRF 검사
 * 포함)을 Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 유효한 CSRF 토큰 + ACL edit 권한으로 POST하면 제출한 NamuMark
 *     source가 0706 `NamuMarkDocumentRenderer`로 실제 HTML(예:
 *     '''굵게''' -> <strong>)까지 렌더링되어 응답 HTML에 포함되고, 아무것도
 *     저장되지 않는지(문서/리비전이 생기지 않는지).
 * (2) CSRF 토큰이 없거나 틀리면 403을 반환하고 미리보기가 렌더링되지
 *     않는지.
 * (3) `GET /wiki/{title}/edit` 편집 화면에는 항상 미리보기 영역
 *     (`id="edit-preview"`)이 존재하는지.
 * (4) 미리보기도 편집과 동일한 ACL edit 권한을 요구한다 — 익명 사용자는
 *     기존 편집 route와 동일하게 `/login`으로 302 리다이렉트되는지.
 * (5) 원본 source에 포함된 HTML 태그는 escape되어 XSS로 이어지지 않는지.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Acl\AclService;
use MintWiki\Acl\DefaultPolicy;
use MintWiki\Acl\Permission as AclPermission;
use MintWiki\Acl\PdoRepository as AclPdoRepository;
use MintWiki\Acl\SubjectType as AclSubjectType;
use MintWiki\Document\Document;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\InMemoryRepository as DocumentInMemoryRepository;
use MintWiki\Document\Repository as DocumentRepository;
use MintWiki\Document\Service as DocumentService;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Render\NamuMarkDocumentRenderer;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\DocumentEditorPage;
use MintWiki\Ui\PermissionDeniedPage;
use MintWiki\User\AccountRepository;

$failures = [];

/**
 * @return array{0: AclSubjectType, 1: ?string}
 */
function mintwiki_preview_test_resolve_subject(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): array
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
 * `public/index.php`가 등록하는 `GET /wiki/{title}/edit`(미리보기 영역
 * 포함)과 `POST /wiki/{title}/preview` 핸들러와 동일한 등록 로직을
 * 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_preview_routes(
    Router $router,
    ?DocumentRepository $documentRepository,
    ?AclPdoRepository $aclRuleRepository,
    AclService $aclService,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    NamuMarkDocumentRenderer $documentRenderer
): void {
    $router->register('GET', '/wiki/{title}/edit', static function (array $params) use ($documentRepository): Response {
        $documentEditorPage = new DocumentEditorPage();
        $requestedTitle = rawurldecode($params['title'] ?? '');

        return Response::html($documentEditorPage->render($requestedTitle, $requestedTitle, '', true));
    });

    $router->register('POST', '/wiki/{title}/preview', static function (array $params) use (
        $documentRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter,
        $documentRenderer
    ): Response {
        $documentEditorPage = new DocumentEditorPage();
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
            [$subjectType, $subjectId] = mintwiki_preview_test_resolve_subject($accountRepository, $sessionAdapter);
            $decision = $aclService->check(AclPermission::Edit, $subjectType, $subjectId, $documentAcl);

            if ($decision->isDenied()) {
                if ($subjectType === AclSubjectType::Anonymous) {
                    return new Response(302, ['Location' => '/login']);
                }

                $permissionDeniedPage = new PermissionDeniedPage();

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
            $previewHtml = $documentRenderer->render($sourceInput)->html();
        }

        return Response::html(
            $documentEditorPage->render($requestedTitle, $titleInput, $sourceInput, $isNew, [], $summaryInput, $previewHtml)
        );
    });
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// account만 실제 sqlite in-memory DB로 검증한다(로그인 사용자 시뮬레이션용) —
// 문서는 ACL과 무관하므로 기존 route 테스트와 동일하게 InMemoryRepository로
// 충분하다.
$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
if ($accountSql === false) {
    fwrite(STDERR, "db/schema/account.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec($accountSql);

$accountRepository = new AccountRepository($pdo);
$regularId = $accountRepository->create('regular', password_hash('irrelevant', PASSWORD_DEFAULT));

$documentRepository = new DocumentInMemoryRepository();
$aclService = new AclService(DefaultPolicy::buildDefaultNamespaceAclDefaults());
$sessionAdapter = new PhpSessionAdapter();
$csrfTokenService = new CsrfTokenService();
$documentRenderer = new NamuMarkDocumentRenderer();

$router = new Router();
mintwiki_register_preview_routes($router, $documentRepository, null, $aclService, $accountRepository, $sessionAdapter, $documentRenderer);

/**
 * 세션에 로그인 사용자를 설정하거나(익명이면 null) 초기화한다.
 */
function mintwiki_preview_test_login(?string $accountId): void
{
    $_SESSION = [];
    if ($accountId !== null) {
        $_SESSION[SessionUserResolver::SESSION_KEY] = $accountId;
    }
}

// (3) 편집 화면에는 항상 미리보기 영역이 존재해야 한다.
$editFormResponse = $router->match(new Request('GET', '/wiki/New Page/edit'))();
if (!str_contains($editFormResponse->body(), 'id="edit-preview"')) {
    $failures[] = '(3) 편집 화면에 미리보기 영역(id="edit-preview")이 존재해야 한다.';
}
if (!str_contains($editFormResponse->body(), 'formaction="/wiki/New%20Page/preview"')) {
    $failures[] = '(3) "미리보기" 버튼은 POST /wiki/{title}/preview를 가리키는 formaction을 가져야 한다.';
}

// (1) 유효한 CSRF 토큰 + 로그인 사용자로 POST하면 렌더링된 HTML을 반환하고
// 아무것도 저장하지 않아야 한다.
mintwiki_preview_test_login($regularId);
$validToken = $csrfTokenService->generate();
$_POST = [
    'title' => 'New Page',
    'source' => "'''굵게''' 내용",
    'summary' => '',
    'csrf_token' => $validToken,
];
$previewResponse = $router->match(new Request('POST', '/wiki/New Page/preview'))();

if ($previewResponse->status() !== 200) {
    $failures[] = '(1) 유효한 미리보기 POST는 200을 반환해야 하는데 ' . $previewResponse->status() . '이었다.';
}
if (!str_contains($previewResponse->body(), '<strong>굵게</strong>')) {
    $failures[] = "(1) 제출한 '''굵게'''가 실제 <strong>으로 렌더링되어 응답에 포함되어야 한다.";
}
if (!str_contains($previewResponse->body(), 'value="New Page"')) {
    $failures[] = '(1) 미리보기 응답에는 제출했던 title 값이 원문 그대로 유지되어야 한다.';
}
if ($documentRepository->getByNormalizedTitle('New Page') !== null) {
    $failures[] = '(1) 미리보기 요청으로 문서가 실제로 저장되면 안 된다.';
}

// (5) 원본 source의 HTML 태그는 escape되어야 한다(XSS 방지).
mintwiki_preview_test_login($regularId);
$xssToken = $csrfTokenService->generate();
$_POST = [
    'title' => 'Xss Preview',
    'source' => '<script>alert(1)</script>',
    'summary' => '',
    'csrf_token' => $xssToken,
];
$xssResponse = $router->match(new Request('POST', '/wiki/Xss Preview/preview'))();
if (str_contains($xssResponse->body(), '<script>alert(1)</script>')) {
    $failures[] = '(5) source에 포함된 script 태그가 escape되지 않고 그대로 렌더링되었다.';
}
if (!str_contains($xssResponse->body(), '&lt;script&gt;alert(1)&lt;/script&gt;')) {
    $failures[] = '(5) source에 포함된 script 태그는 escape된 형태로 표시되어야 한다.';
}

// (2) CSRF 토큰이 없거나 틀리면 403을 반환하고 미리보기가 렌더링되지 않아야 한다.
mintwiki_preview_test_login($regularId);
$_POST = [
    'title' => 'Csrf Rejected',
    'source' => "'''중요''' 내용",
    'summary' => '',
    'csrf_token' => 'invalid-token',
];
$csrfRejectedResponse = $router->match(new Request('POST', '/wiki/Csrf Rejected/preview'))();
if ($csrfRejectedResponse->status() !== 403) {
    $failures[] = '(2) CSRF 토큰이 유효하지 않으면 403을 반환해야 하는데 ' . $csrfRejectedResponse->status() . '이었다.';
}
if (str_contains($csrfRejectedResponse->body(), '<strong>중요</strong>')) {
    $failures[] = '(2) CSRF 검증에 실패하면 미리보기가 렌더링되면 안 된다.';
}
if (!str_contains($csrfRejectedResponse->body(), '유효하지 않은 요청입니다')) {
    $failures[] = '(2) CSRF 검증 실패 응답에는 오류 메시지가 표시되어야 한다.';
}

mintwiki_preview_test_login($regularId);
$_POST = [
    'title' => 'Csrf Missing',
    'source' => '내용',
    'summary' => '',
    'csrf_token' => '',
];
$csrfMissingResponse = $router->match(new Request('POST', '/wiki/Csrf Missing/preview'))();
if ($csrfMissingResponse->status() !== 403) {
    $failures[] = '(2) CSRF 토큰이 없으면 403을 반환해야 하는데 ' . $csrfMissingResponse->status() . '이었다.';
}

// (4) 미리보기도 편집과 동일한 ACL edit 권한을 요구한다 — 익명은 기존 편집
// route와 동일하게 /login으로 302 리다이렉트되어야 한다.
mintwiki_preview_test_login(null);
$anonToken = $csrfTokenService->generate();
$_POST = [
    'title' => 'Anon Preview Attempt',
    'source' => '익명 편집 시도',
    'summary' => '',
    'csrf_token' => $anonToken,
];
$anonResponse = $router->match(new Request('POST', '/wiki/Anon Preview Attempt/preview'))();
if ($anonResponse->status() !== 302 || ($anonResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(4) 익명 사용자의 미리보기 POST는 /login으로 302여야 하는데 그렇지 않았다(status=' . $anonResponse->status() . ').';
}
if ($documentRepository->getByNormalizedTitle('Anon Preview Attempt') !== null) {
    $failures[] = '(4) 익명 사용자의 미리보기 요청으로 문서가 저장되면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "POST /wiki/{title}/preview route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "POST /wiki/{title}/preview route 테스트 통과.\n");
exit(0);
