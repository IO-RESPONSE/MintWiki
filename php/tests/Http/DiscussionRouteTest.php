<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0712에서 등록하는
 * `GET`/`POST /wiki/{title}/discussion`과
 * `POST /wiki/{title}/discussion/{threadId}/comment`를 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다(0710 `DocumentHistoryDiffRouteTest.php`와
 * 동일한 방식) — index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록
 * 로직(ACL 검사 포함)을 Router에 그대로 재구성해 검증한다. 문서/계정/ACL
 * 규칙/스레드/댓글은 실제 sqlite in-memory PDO로 만든다 —
 * `discussion_thread.document_id`가 `document.id`를 FK로 참조하므로 실제
 * 문서 행이 필요하다.
 *
 * 검증 대상:
 * (1) GET은 스레드/댓글을 렌더링하고, 스레드/댓글이 없으면 빈 상태를
 *     안전하게 렌더링한다.
 * (2) discuss 권한이 없으면(acl_rule 없음, 로그인 사용자도 포함) GET은
 *     새 스레드/댓글 form 대신 로그인 안내를 보여준다 — discuss는 read와
 *     달리 규칙이 없으면 기본적으로 거부된다.
 * (3) 읽기 권한이 없는 문서는 GET이 403(PermissionDeniedPage)을 반환한다.
 * (4) 새 스레드 POST: 익명은 /login으로 302, discuss 권한 없는 로그인
 *     사용자는 403, CSRF 실패는 403, 빈 제목은 422, 성공하면 스레드가
 *     저장되고 discussion page로 302 리다이렉트된다.
 * (5) 댓글 POST: 위와 동일한 ACL/CSRF/검증 규칙을 따르고, 성공하면 댓글이
 *     저장된다. 존재하지 않거나 다른 문서 소속인 threadId는 404를 반환한다.
 * (6) `$documentRepository`가 없으면(DB 미설정/오류) 세 route 모두 404를
 *     반환한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Acl\AclService;
use MintWiki\Acl\DefaultPolicy;
use MintWiki\Acl\NamespaceAclDefaults;
use MintWiki\Acl\PdoRepository as AclPdoRepository;
use MintWiki\Acl\Permission as AclPermission;
use MintWiki\Acl\SubjectType as AclSubjectType;
use MintWiki\Discussion\EmptyCommentBodyError;
use MintWiki\Discussion\EmptyThreadTitleError;
use MintWiki\Discussion\PdoRepository as DiscussionPdoRepository;
use MintWiki\Discussion\Service as DiscussionService;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\PdoRepository as DocumentPdoRepository;
use MintWiki\Document\Repository as DocumentRepository;
use MintWiki\Document\Service as DocumentService;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\DiscussionPage;
use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\PermissionDeniedPage;
use MintWiki\User\AccountRepository;

$failures = [];

/**
 * @return array{0: AclSubjectType, 1: ?string}
 */
function mintwiki_discussion_test_resolve_subject(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): array
{
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return [AclSubjectType::User, $currentUser->id()];
        }
    }

    return [AclSubjectType::Anonymous, null];
}

function mintwiki_discussion_test_created_by(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): string
{
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return $currentUser->username();
        }
    }

    return 'anonymous';
}

/**
 * @return array{0: array<int, \MintWiki\Discussion\Thread>, 1: array<string, array<int, \MintWiki\Discussion\Comment>>}
 */
function mintwiki_discussion_test_load_data(?PDO $pdo, string $documentId): array
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
 * `public/index.php`가 0712에서 등록하는 `GET`/`POST /wiki/{title}/discussion`,
 * `POST /wiki/{title}/discussion/{threadId}/comment` 핸들러와 동일한 등록
 * 로직을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_discussion_routes(
    Router $router,
    ?DocumentRepository $documentRepository,
    ?AclPdoRepository $aclRuleRepository,
    AclService $aclService,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    ?PDO $pdo
): void {
    $router->register('GET', '/wiki/{title}/discussion', static function (array $params) use (
        $documentRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter,
        $pdo
    ): Response {
        $requestedTitle = rawurldecode($params['title'] ?? '');

        if ($documentRepository === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/discussion'), 404);
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/discussion'), 404);
        }

        $documentAcl = $aclRuleRepository?->documentAcl($document->id());
        [$subjectType, $subjectId] = mintwiki_discussion_test_resolve_subject($accountRepository, $sessionAdapter);
        $readDecision = $aclService->check(AclPermission::Read, $subjectType, $subjectId, $documentAcl);

        if ($readDecision->isDenied()) {
            return Response::html((new PermissionDeniedPage())->render($readDecision), 403);
        }

        $discussDecision = $aclService->check(AclPermission::Discuss, $subjectType, $subjectId, $documentAcl);

        [$threads, $commentsByThreadId] = mintwiki_discussion_test_load_data($pdo, $document->id());

        return Response::html(
            (new DiscussionPage())->render($document, $threads, $commentsByThreadId, [], [], $discussDecision->isAllowed())
        );
    });

    $router->register('POST', '/wiki/{title}/discussion', static function (array $params) use (
        $documentRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter,
        $pdo
    ): Response {
        $requestedTitle = rawurldecode($params['title'] ?? '');
        $csrfTokenService = new CsrfTokenService();

        $titleInput = is_string($_POST['title'] ?? null) ? $_POST['title'] : '';
        $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

        if ($documentRepository === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/discussion'), 404);
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/discussion'), 404);
        }

        $documentAcl = $aclRuleRepository?->documentAcl($document->id());
        [$subjectType, $subjectId] = mintwiki_discussion_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Discuss, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            if ($subjectType === AclSubjectType::Anonymous) {
                return new Response(302, ['Location' => '/login']);
            }

            return Response::html((new PermissionDeniedPage())->render($decision), 403);
        }

        [$threads, $commentsByThreadId] = mintwiki_discussion_test_load_data($pdo, $document->id());
        $discussionPage = new DiscussionPage();

        if (!$csrfTokenService->validate($csrfToken)) {
            return Response::html(
                $discussionPage->render($document, $threads, $commentsByThreadId, [
                    '_form' => '유효하지 않은 요청입니다. 다시 시도하세요.',
                ], [], true),
                403
            );
        }

        $discussionService = new DiscussionService(new DiscussionPdoRepository($pdo));
        $createdBy = mintwiki_discussion_test_created_by($accountRepository, $sessionAdapter);

        try {
            $discussionService->createThread($document->id(), $titleInput, $createdBy);
        } catch (EmptyThreadTitleError) {
            return Response::html(
                $discussionPage->render($document, $threads, $commentsByThreadId, [
                    'title' => '스레드 제목을 입력하세요.',
                ], [], true),
                422
            );
        }

        return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title()) . '/discussion']);
    });

    $router->register('POST', '/wiki/{title}/discussion/{threadId}/comment', static function (array $params) use (
        $documentRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter,
        $pdo
    ): Response {
        $requestedTitle = rawurldecode($params['title'] ?? '');
        $threadId = $params['threadId'] ?? '';
        $csrfTokenService = new CsrfTokenService();

        $bodyInput = is_string($_POST['body'] ?? null) ? $_POST['body'] : '';
        $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

        if ($documentRepository === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/discussion'), 404);
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/discussion'), 404);
        }

        $documentAcl = $aclRuleRepository?->documentAcl($document->id());
        [$subjectType, $subjectId] = mintwiki_discussion_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Discuss, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            if ($subjectType === AclSubjectType::Anonymous) {
                return new Response(302, ['Location' => '/login']);
            }

            return Response::html((new PermissionDeniedPage())->render($decision), 403);
        }

        $discussionService = new DiscussionService(new DiscussionPdoRepository($pdo));
        $thread = $discussionService->getThread($threadId);

        if ($thread === null || $thread->documentId() !== $document->id()) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/discussion'), 404);
        }

        [$threads, $commentsByThreadId] = mintwiki_discussion_test_load_data($pdo, $document->id());
        $discussionPage = new DiscussionPage();

        if (!$csrfTokenService->validate($csrfToken)) {
            return Response::html(
                $discussionPage->render($document, $threads, $commentsByThreadId, [], [
                    $threadId => ['_form' => '유효하지 않은 요청입니다. 다시 시도하세요.'],
                ], true),
                403
            );
        }

        $createdBy = mintwiki_discussion_test_created_by($accountRepository, $sessionAdapter);

        try {
            $discussionService->addComment($threadId, $bodyInput, $createdBy);
        } catch (EmptyCommentBodyError) {
            return Response::html(
                $discussionPage->render($document, $threads, $commentsByThreadId, [], [
                    $threadId => ['body' => '댓글 본문을 입력하세요.'],
                ], true),
                422
            );
        }

        return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title()) . '/discussion']);
    });
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

/**
 * 세션에 로그인 사용자를 설정하거나(익명이면 null) 초기화한다.
 */
function mintwiki_discussion_test_login(?string $accountId): void
{
    $_SESSION = [];
    if ($accountId !== null) {
        $_SESSION[SessionUserResolver::SESSION_KEY] = $accountId;
    }
}

$documentSql = file_get_contents(__DIR__ . '/../../../db/schema/document.sql');
$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_rule.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');
$discussionThreadSql = file_get_contents(__DIR__ . '/../../../db/schema/discussion_thread.sql');
$discussionCommentSql = file_get_contents(__DIR__ . '/../../../db/schema/discussion_comment.sql');

if (
    $documentSql === false || $accountSql === false || $aclRuleSql === false
    || $aclNamespaceRuleSql === false || $discussionThreadSql === false || $discussionCommentSql === false
) {
    fwrite(STDERR, "db/schema/*.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec('PRAGMA foreign_keys = ON');
$pdo->exec($documentSql);
$pdo->exec($accountSql);
$pdo->exec($aclRuleSql);
$pdo->exec($aclNamespaceRuleSql);
$pdo->exec($discussionThreadSql);
$pdo->exec($discussionCommentSql);

$documentRepository = new DocumentPdoRepository($pdo);
$documentService = new DocumentService($documentRepository);
$accountRepository = new AccountRepository($pdo);
$aclRuleRepository = new AclPdoRepository($pdo);
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
$aclService = new AclService($namespaceAclDefaults);
$sessionAdapter = new PhpSessionAdapter();
$csrfTokenService = new CsrfTokenService();

$memberId = $accountRepository->create('member', password_hash('irrelevant', PASSWORD_DEFAULT));
$outsiderId = $accountRepository->create('outsider', password_hash('irrelevant', PASSWORD_DEFAULT));

// discussableDoc: 문서별 acl_rule로 read는 모두 허용, discuss는 member만 허용한다.
$discussableDoc = $documentService->create('Discussable Doc');
$insertRule = $pdo->prepare(
    'INSERT INTO acl_rule (id, document_id, subject_type, subject_id, permission, effect, expires_at, sort_order) '
    . 'VALUES (:id, :document_id, :subject_type, :subject_id, :permission, :effect, NULL, :sort_order)'
);
$insertRule->execute(['id' => 'rule-discussable-read-all', 'document_id' => $discussableDoc->id(), 'subject_type' => 'all', 'subject_id' => null, 'permission' => 'read', 'effect' => 'allow', 'sort_order' => 0]);
$insertRule->execute(['id' => 'rule-discussable-discuss-member', 'document_id' => $discussableDoc->id(), 'subject_type' => 'user', 'subject_id' => $memberId, 'permission' => 'discuss', 'effect' => 'allow', 'sort_order' => 1]);

// openDoc: acl_rule이 전혀 없다 — read는 네임스페이스 기본값(공개)이지만
// discuss는 규칙이 없어 로그인 여부와 무관하게 항상 거부되어야 한다.
$openDoc = $documentService->create('Open Doc');

// lockedDoc: 전체 읽기 거부.
$lockedDoc = $documentService->create('Locked Doc');
$insertRule->execute(['id' => 'rule-locked-read-deny', 'document_id' => $lockedDoc->id(), 'subject_type' => 'all', 'subject_id' => null, 'permission' => 'read', 'effect' => 'deny', 'sort_order' => 0]);

$router = new Router();
mintwiki_register_discussion_routes($router, $documentRepository, $aclRuleRepository, $aclService, $accountRepository, $sessionAdapter, $pdo);

// (1)/(2) 빈 상태 + discuss 권한 없음(로그인 여부 무관) 렌더링.
mintwiki_discussion_test_login(null);
$openAnonResponse = $router->match(new Request('GET', '/wiki/Open Doc/discussion'))();
if ($openAnonResponse->status() !== 200) {
    $failures[] = "(1) openDoc 익명 GET은 200이어야 하는데 {$openAnonResponse->status()}이었다.";
}
if (!str_contains($openAnonResponse->body(), 'thread 없음')) {
    $failures[] = '(1) 스레드가 없는 문서는 "thread 없음"을 표시해야 한다.';
}
if (!str_contains($openAnonResponse->body(), '로그인이 필요합니다')) {
    $failures[] = '(2) discuss 권한이 없는 익명 사용자는 로그인 안내를 봐야 한다.';
}
if (str_contains($openAnonResponse->body(), '<form method="post"')) {
    $failures[] = '(2) discuss 권한이 없으면 새 스레드/댓글 form을 보여주면 안 된다.';
}

mintwiki_discussion_test_login($outsiderId);
$openOutsiderResponse = $router->match(new Request('GET', '/wiki/Open Doc/discussion'))();
if ($openOutsiderResponse->status() !== 200) {
    $failures[] = "(2) openDoc 로그인 사용자 GET은 200이어야 하는데 {$openOutsiderResponse->status()}이었다.";
}
if (!str_contains($openOutsiderResponse->body(), '로그인이 필요합니다')) {
    $failures[] = '(2) acl_rule이 전혀 없으면 로그인한 사용자도 discuss가 거부되어야 한다(규칙 없음 = 거부 기본값).';
}

// (3) 읽기 거부된 문서는 GET이 403이어야 한다.
foreach (['anonymous' => null, 'member' => $memberId] as $label => $accountId) {
    mintwiki_discussion_test_login($accountId);
    $lockedResponse = $router->match(new Request('GET', '/wiki/Locked Doc/discussion'))();
    if ($lockedResponse->status() !== 403) {
        $failures[] = "(3) {$label}의 잠긴 문서 discussion GET은 403이어야 하는데 {$lockedResponse->status()}이었다.";
    }
}

// (4) 새 스레드 POST: 익명 -> /login, discuss 권한 없는 로그인 사용자 -> 403.
mintwiki_discussion_test_login(null);
$_POST = ['title' => '익명 시도', 'csrf_token' => 'irrelevant'];
$anonThreadResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion'))();
if ($anonThreadResponse->status() !== 302 || ($anonThreadResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(4) 익명 사용자의 새 스레드 POST는 /login으로 302여야 하는데 그렇지 않았다(status=' . $anonThreadResponse->status() . ').';
}

mintwiki_discussion_test_login($outsiderId);
$outsiderToken = $csrfTokenService->generate();
$_POST = ['title' => '아웃사이더 시도', 'csrf_token' => $outsiderToken];
$outsiderThreadResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion'))();
if ($outsiderThreadResponse->status() !== 403) {
    $failures[] = '(4) discuss 권한이 없는 로그인 사용자의 새 스레드 POST는 403이어야 하는데 ' . $outsiderThreadResponse->status() . '이었다.';
}

// member: CSRF 실패 -> 403, 아무것도 저장되지 않음.
mintwiki_discussion_test_login($memberId);
$_POST = ['title' => 'CSRF로 거부될 스레드', 'csrf_token' => 'invalid-token'];
$csrfRejectedThreadResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion'))();
if ($csrfRejectedThreadResponse->status() !== 403) {
    $failures[] = '(4) CSRF 토큰이 유효하지 않은 새 스레드 POST는 403이어야 하는데 ' . $csrfRejectedThreadResponse->status() . '이었다.';
}
[$threadsAfterCsrfReject] = mintwiki_discussion_test_load_data($pdo, $discussableDoc->id());
if ($threadsAfterCsrfReject !== []) {
    $failures[] = '(4) CSRF 검증에 실패하면 스레드가 저장되면 안 된다.';
}

// member: 빈 제목 -> 422.
$emptyTitleToken = $csrfTokenService->generate();
$_POST = ['title' => '   ', 'csrf_token' => $emptyTitleToken];
$emptyTitleResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion'))();
if ($emptyTitleResponse->status() !== 422) {
    $failures[] = '(4) 빈 제목으로 POST하면 422를 반환해야 하는데 ' . $emptyTitleResponse->status() . '이었다.';
}
if (!str_contains($emptyTitleResponse->body(), '스레드 제목을 입력하세요.')) {
    $failures[] = '(4) 빈 제목 오류 메시지가 폼에 표시되어야 한다.';
}

// member: 유효한 CSRF + 제목 -> 302 + 스레드 저장.
$validThreadToken = $csrfTokenService->generate();
$_POST = ['title' => '첫 번째 토론 주제', 'csrf_token' => $validThreadToken];
$createThreadResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion'))();
if ($createThreadResponse->status() !== 302) {
    $failures[] = '(4) 유효한 새 스레드 POST는 302를 반환해야 하는데 ' . $createThreadResponse->status() . '이었다.';
}
if (($createThreadResponse->headers()['Location'] ?? null) !== '/wiki/Discussable%20Doc/discussion') {
    $failures[] = '(4) 새 스레드 POST 성공 시 Location은 /wiki/{title}/discussion이어야 한다.';
}

[$threadsAfterCreate] = mintwiki_discussion_test_load_data($pdo, $discussableDoc->id());
if (count($threadsAfterCreate) !== 1) {
    $failures[] = '(4) 유효한 POST 이후 스레드가 정확히 1개 저장되어 있어야 한다.';
} elseif ($threadsAfterCreate[0]->title() !== '첫 번째 토론 주제' || $threadsAfterCreate[0]->createdBy() !== 'member') {
    $failures[] = '(4) 저장된 스레드의 제목/작성자가 제출한 값과 일치해야 한다.';
}
$thread = $threadsAfterCreate[0];

// (1) GET으로 방금 만든 스레드가 보이는지, 댓글이 없으면 "댓글 없음"인지 확인.
$discussionWithThreadResponse = $router->match(new Request('GET', '/wiki/Discussable Doc/discussion'))();
if (!str_contains($discussionWithThreadResponse->body(), '첫 번째 토론 주제')) {
    $failures[] = '(1) GET 응답에 방금 만든 스레드 제목이 보여야 한다.';
}
if (!str_contains($discussionWithThreadResponse->body(), '댓글 없음')) {
    $failures[] = '(1) 댓글이 없는 스레드는 "댓글 없음"을 표시해야 한다.';
}

// (5) 댓글 POST: 익명 -> /login, discuss 권한 없음 -> 403, CSRF 실패 -> 403,
// 빈 본문 -> 422, 성공 -> 302 + 저장. 존재하지 않거나 다른 문서 소속
// threadId는 404.
mintwiki_discussion_test_login(null);
$_POST = ['body' => '익명 댓글 시도', 'csrf_token' => 'irrelevant'];
$anonCommentResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion/' . $thread->id() . '/comment'))();
if ($anonCommentResponse->status() !== 302 || ($anonCommentResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(5) 익명 사용자의 댓글 POST는 /login으로 302여야 하는데 그렇지 않았다(status=' . $anonCommentResponse->status() . ').';
}

mintwiki_discussion_test_login($outsiderId);
$outsiderCommentToken = $csrfTokenService->generate();
$_POST = ['body' => '아웃사이더 댓글 시도', 'csrf_token' => $outsiderCommentToken];
$outsiderCommentResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion/' . $thread->id() . '/comment'))();
if ($outsiderCommentResponse->status() !== 403) {
    $failures[] = '(5) discuss 권한이 없는 로그인 사용자의 댓글 POST는 403이어야 하는데 ' . $outsiderCommentResponse->status() . '이었다.';
}

mintwiki_discussion_test_login($memberId);
$_POST = ['body' => 'CSRF로 거부될 댓글', 'csrf_token' => 'invalid-token'];
$csrfRejectedCommentResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion/' . $thread->id() . '/comment'))();
if ($csrfRejectedCommentResponse->status() !== 403) {
    $failures[] = '(5) CSRF 토큰이 유효하지 않은 댓글 POST는 403이어야 하는데 ' . $csrfRejectedCommentResponse->status() . '이었다.';
}
[, $commentsAfterCsrfReject] = mintwiki_discussion_test_load_data($pdo, $discussableDoc->id());
if (($commentsAfterCsrfReject[$thread->id()] ?? []) !== []) {
    $failures[] = '(5) CSRF 검증에 실패하면 댓글이 저장되면 안 된다.';
}

$emptyBodyToken = $csrfTokenService->generate();
$_POST = ['body' => '   ', 'csrf_token' => $emptyBodyToken];
$emptyBodyResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion/' . $thread->id() . '/comment'))();
if ($emptyBodyResponse->status() !== 422) {
    $failures[] = '(5) 빈 본문으로 댓글 POST하면 422를 반환해야 하는데 ' . $emptyBodyResponse->status() . '이었다.';
}
if (!str_contains($emptyBodyResponse->body(), '댓글 본문을 입력하세요.')) {
    $failures[] = '(5) 빈 본문 오류 메시지가 폼에 표시되어야 한다.';
}

$validCommentToken = $csrfTokenService->generate();
$_POST = ['body' => '첫 댓글입니다', 'csrf_token' => $validCommentToken];
$createCommentResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion/' . $thread->id() . '/comment'))();
if ($createCommentResponse->status() !== 302) {
    $failures[] = '(5) 유효한 댓글 POST는 302를 반환해야 하는데 ' . $createCommentResponse->status() . '이었다.';
}
if (($createCommentResponse->headers()['Location'] ?? null) !== '/wiki/Discussable%20Doc/discussion') {
    $failures[] = '(5) 댓글 POST 성공 시 Location은 /wiki/{title}/discussion이어야 한다.';
}

[, $commentsAfterCreate] = mintwiki_discussion_test_load_data($pdo, $discussableDoc->id());
$threadComments = $commentsAfterCreate[$thread->id()] ?? [];
if (count($threadComments) !== 1) {
    $failures[] = '(5) 유효한 POST 이후 댓글이 정확히 1개 저장되어 있어야 한다.';
} elseif ($threadComments[0]->body() !== '첫 댓글입니다' || $threadComments[0]->createdBy() !== 'member') {
    $failures[] = '(5) 저장된 댓글의 본문/작성자가 제출한 값과 일치해야 한다.';
}

// GET으로 방금 만든 댓글이 보이는지 확인.
$discussionWithCommentResponse = $router->match(new Request('GET', '/wiki/Discussable Doc/discussion'))();
if (!str_contains($discussionWithCommentResponse->body(), '첫 댓글입니다')) {
    $failures[] = '(1) GET 응답에 방금 만든 댓글 본문이 보여야 한다.';
}

// 존재하지 않는 threadId -> 404.
$missingThreadToken = $csrfTokenService->generate();
$_POST = ['body' => '아무 댓글', 'csrf_token' => $missingThreadToken];
$missingThreadResponse = $router->match(new Request('POST', '/wiki/Discussable Doc/discussion/no-such-thread/comment'))();
if ($missingThreadResponse->status() !== 404) {
    $failures[] = '(5) 존재하지 않는 threadId로 댓글 POST하면 404여야 하는데 ' . $missingThreadResponse->status() . '이었다.';
}

// 다른 문서 소속 threadId -> 404 (openDoc의 discussion URL로 discussableDoc의 thread id를 섞는다).
$insertRule->execute(['id' => 'rule-open-discuss-member', 'document_id' => $openDoc->id(), 'subject_type' => 'user', 'subject_id' => $memberId, 'permission' => 'discuss', 'effect' => 'allow', 'sort_order' => 0]);
$crossDocToken = $csrfTokenService->generate();
$_POST = ['body' => '다른 문서 댓글 시도', 'csrf_token' => $crossDocToken];
$crossDocResponse = $router->match(new Request('POST', '/wiki/Open Doc/discussion/' . $thread->id() . '/comment'))();
if ($crossDocResponse->status() !== 404) {
    $failures[] = '(5) 다른 문서 소속 threadId를 섞은 댓글 POST는 404여야 하는데 ' . $crossDocResponse->status() . '이었다.';
}

// (6) 문서가 없으면(DB 미설정/오류 상황과 동일하게 취급) 세 route 모두 404.
$unconfiguredRouter = new Router();
mintwiki_register_discussion_routes($unconfiguredRouter, null, null, $aclService, null, $sessionAdapter, null);

$unconfiguredGetResponse = $unconfiguredRouter->match(new Request('GET', '/wiki/Anything/discussion'))();
if ($unconfiguredGetResponse->status() !== 404) {
    $failures[] = '(6) documentRepository가 없으면 GET /wiki/{title}/discussion은 404여야 하는데 ' . $unconfiguredGetResponse->status() . '이었다.';
}

$_POST = ['title' => 'Anything', 'csrf_token' => 'irrelevant'];
$unconfiguredThreadPostResponse = $unconfiguredRouter->match(new Request('POST', '/wiki/Anything/discussion'))();
if ($unconfiguredThreadPostResponse->status() !== 404) {
    $failures[] = '(6) documentRepository가 없으면 POST /wiki/{title}/discussion은 404여야 하는데 ' . $unconfiguredThreadPostResponse->status() . '이었다.';
}

$_POST = ['body' => 'Anything', 'csrf_token' => 'irrelevant'];
$unconfiguredCommentPostResponse = $unconfiguredRouter->match(new Request('POST', '/wiki/Anything/discussion/thread-1/comment'))();
if ($unconfiguredCommentPostResponse->status() !== 404) {
    $failures[] = '(6) documentRepository가 없으면 POST /wiki/{title}/discussion/{threadId}/comment는 404여야 하는데 ' . $unconfiguredCommentPostResponse->status() . '이었다.';
}
$_POST = [];

if ($failures !== []) {
    fwrite(STDERR, "GET/POST /wiki/{title}/discussion, POST /wiki/{title}/discussion/{threadId}/comment route 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET/POST /wiki/{title}/discussion, POST /wiki/{title}/discussion/{threadId}/comment route 테스트 통과.\n");
exit(0);
