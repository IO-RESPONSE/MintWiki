<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0715에서 등록하는
 * `GET`/`POST /wiki/{title}/delete`를 확인하는 smoke test. phpunit 없이
 * `php` CLI만으로 실행된다(0710 `DocumentHistoryDiffRouteTest.php`와 동일한
 * 방식) — index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록 로직(ACL
 * 검사 + CSRF + 확인 체크박스 + 감사 기록 포함)을 Router에 그대로 재구성해
 * 검증한다. 문서/계정/ACL 규칙은 실제 sqlite in-memory PDO로 만든다.
 *
 * 검증 대상:
 * (1) GET: 삭제 권한이 있는 로그인 사용자에게는 확인 화면(체크박스 + CSRF
 *     토큰)을 보여준다.
 * (2) GET/POST: 익명은 `/login`으로 302, delete 권한이 없는 로그인 사용자는
 *     403을 반환한다(default policy는 로그인 사용자에게 delete를 허용하므로,
 *     문서별 acl_rule로 명시적으로 거부한 문서를 사용해 검증한다).
 * (3) GET/POST: 존재하지 않는 문서는 404를 반환한다.
 * (4) POST: CSRF 검증에 실패하면 403이고 문서는 그대로 남는다.
 * (5) POST: 확인 체크박스(`confirm_delete`)가 없으면 422이고 문서는 그대로
 *     남는다.
 * (6) POST: 모든 검증을 통과하면 문서(및 리비전/토론/acl_rule)가 삭제되고
 *     `/`로 302 리다이렉트되며, module=document, action=deleted 감사
 *     이벤트가 entity_id=문서 id, actor_id=로그인 계정 id로 기록된다.
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
use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\PdoAuditRecorder;
use MintWiki\Audit\RecentAuditEventsQuery;
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
use MintWiki\Ui\DocumentDeletePage;
use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\PermissionDeniedPage;
use MintWiki\User\AccountRepository;

$failures = [];

/**
 * @return array{0: AclSubjectType, 1: ?string}
 */
function mintwiki_delete_test_resolve_subject(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): array
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
 * `public/index.php`가 0715에서 등록하는 `GET`/`POST /wiki/{title}/delete`
 * 핸들러와 동일한 등록 로직을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_delete_routes(
    Router $router,
    ?DocumentRepository $documentRepository,
    ?AclPdoRepository $aclRuleRepository,
    AclService $aclService,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    PdoAuditRecorder $auditRecorder
): void {
    $router->register('GET', '/wiki/{title}/delete', static function (array $params) use (
        $documentRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter
    ): Response {
        $requestedTitle = rawurldecode($params['title'] ?? '');

        if ($documentRepository === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/delete'), 404);
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/delete'), 404);
        }

        $documentAcl = $aclRuleRepository?->documentAcl($document->id());
        [$subjectType, $subjectId] = mintwiki_delete_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Delete, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            if ($subjectType === AclSubjectType::Anonymous) {
                return new Response(302, ['Location' => '/login']);
            }

            return Response::html((new PermissionDeniedPage())->render($decision), 403);
        }

        return Response::html((new DocumentDeletePage())->render($document->title()));
    });

    $router->register('POST', '/wiki/{title}/delete', static function (array $params) use (
        $documentRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter,
        $auditRecorder
    ): Response {
        $requestedTitle = rawurldecode($params['title'] ?? '');

        if ($documentRepository === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/delete'), 404);
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/delete'), 404);
        }

        $documentAcl = $aclRuleRepository?->documentAcl($document->id());
        [$subjectType, $subjectId] = mintwiki_delete_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Delete, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            if ($subjectType === AclSubjectType::Anonymous) {
                return new Response(302, ['Location' => '/login']);
            }

            return Response::html((new PermissionDeniedPage())->render($decision), 403);
        }

        $documentDeletePage = new DocumentDeletePage();
        $csrfToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';

        if (!(new CsrfTokenService())->validate($csrfToken)) {
            return Response::html(
                $documentDeletePage->render($document->title(), ['_form' => '유효하지 않은 요청입니다. 다시 시도하세요.']),
                403
            );
        }

        if (($_POST['confirm_delete'] ?? null) !== '1') {
            return Response::html(
                $documentDeletePage->render($document->title(), [
                    'confirm_delete' => '삭제를 실행하려면 위험 작업 확인에 동의해야 합니다.',
                ]),
                422
            );
        }

        $documentService->delete($document->id());

        try {
            $auditRecorder->record(new AuditEvent(
                id: bin2hex(random_bytes(16)),
                module: 'document',
                action: 'deleted',
                occurredAt: new \DateTimeImmutable('now'),
                actorId: $subjectType === AclSubjectType::Anonymous ? 'anonymous' : $subjectId,
                metadata: ['entity_id' => $document->id()]
            ));
        } catch (\Throwable $exception) {
            \error_log('Audit recording failed: ' . $exception->getMessage());
        }

        return new Response(302, ['Location' => '/']);
    });
}

function mintwiki_delete_test_login(?string $accountId): void
{
    $_SESSION = [];
    if ($accountId !== null) {
        $_SESSION[SessionUserResolver::SESSION_KEY] = $accountId;
    }
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$documentSql = file_get_contents(__DIR__ . '/../../../db/schema/document.sql');
$revisionSql = file_get_contents(__DIR__ . '/../../../db/schema/revision.sql');
$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_rule.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');
$discussionThreadSql = file_get_contents(__DIR__ . '/../../../db/schema/discussion_thread.sql');
$discussionCommentSql = file_get_contents(__DIR__ . '/../../../db/schema/discussion_comment.sql');
$auditEventSql = file_get_contents(__DIR__ . '/../../../db/schema/audit_event.sql');

if (
    $documentSql === false || $revisionSql === false || $accountSql === false || $aclRuleSql === false
    || $aclNamespaceRuleSql === false || $discussionThreadSql === false || $discussionCommentSql === false
    || $auditEventSql === false
) {
    fwrite(STDERR, "db/schema/*.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec('PRAGMA foreign_keys = ON');
$pdo->exec($documentSql);
$pdo->exec($revisionSql);
$pdo->exec($accountSql);
$pdo->exec($aclRuleSql);
$pdo->exec($aclNamespaceRuleSql);
$pdo->exec($discussionThreadSql);
$pdo->exec($discussionCommentSql);
$pdo->exec($auditEventSql);

$documentRepository = new DocumentPdoRepository($pdo);
$documentService = new DocumentService($documentRepository);
$accountRepository = new AccountRepository($pdo);
$aclRuleRepository = new AclPdoRepository($pdo);
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
$aclService = new AclService($namespaceAclDefaults);
$sessionAdapter = new PhpSessionAdapter();
$csrfTokenService = new CsrfTokenService();
$auditRecorder = new PdoAuditRecorder($pdo);
$auditQuery = new RecentAuditEventsQuery($pdo);

$memberId = $accountRepository->create('member', password_hash('irrelevant', PASSWORD_DEFAULT));
$outsiderId = $accountRepository->create('outsider', password_hash('irrelevant', PASSWORD_DEFAULT));

// openDoc: acl_rule이 전혀 없다 — delete는 기본 정책상 익명 거부/로그인 허용.
$openDoc = $documentService->create('Open Doc');

// lockedDoc: 문서별 acl_rule로 delete를 outsider에게 명시적으로 거부한다.
$lockedDoc = $documentService->create('Locked Doc');
$insertRule = $pdo->prepare(
    'INSERT INTO acl_rule (id, document_id, subject_type, subject_id, permission, effect, expires_at, sort_order) '
    . 'VALUES (:id, :document_id, :subject_type, :subject_id, :permission, :effect, NULL, :sort_order)'
);
$insertRule->execute(['id' => 'rule-locked-delete-deny', 'document_id' => $lockedDoc->id(), 'subject_type' => 'user', 'subject_id' => $outsiderId, 'permission' => 'delete', 'effect' => 'deny', 'sort_order' => 0]);

$router = new Router();
mintwiki_register_delete_routes($router, $documentRepository, $aclRuleRepository, $aclService, $accountRepository, $sessionAdapter, $auditRecorder);

// (1) 삭제 권한이 있는 로그인 사용자는 확인 화면(체크박스 + CSRF 토큰)을 본다.
mintwiki_delete_test_login($memberId);
$getResponse = $router->match(new Request('GET', '/wiki/Open Doc/delete'))();
if ($getResponse->status() !== 200) {
    $failures[] = "(1) 삭제 권한이 있는 사용자의 GET은 200이어야 하는데 {$getResponse->status()}이었다.";
}
if (!str_contains($getResponse->body(), 'name="confirm_delete"')) {
    $failures[] = '(1) 확인 화면에 confirm_delete 체크박스가 있어야 한다.';
}
if (!str_contains($getResponse->body(), 'name="csrf_token"')) {
    $failures[] = '(1) 확인 화면에 csrf_token hidden 필드가 있어야 한다.';
}

// (2) 익명은 GET/POST 모두 /login으로 302.
mintwiki_delete_test_login(null);
$anonGetResponse = $router->match(new Request('GET', '/wiki/Open Doc/delete'))();
if ($anonGetResponse->status() !== 302 || ($anonGetResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(2) 익명 사용자의 GET은 /login으로 302여야 한다.';
}
$_POST = ['csrf_token' => 'irrelevant', 'confirm_delete' => '1'];
$anonPostResponse = $router->match(new Request('POST', '/wiki/Open Doc/delete'))();
if ($anonPostResponse->status() !== 302 || ($anonPostResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(2) 익명 사용자의 POST는 /login으로 302여야 한다.';
}

// (2) delete 권한이 없는 로그인 사용자(outsider)는 GET/POST 모두 403.
mintwiki_delete_test_login($outsiderId);
$deniedGetResponse = $router->match(new Request('GET', '/wiki/Locked Doc/delete'))();
if ($deniedGetResponse->status() !== 403) {
    $failures[] = '(2) delete 권한이 없는 사용자의 GET은 403이어야 하는데 ' . $deniedGetResponse->status() . '이었다.';
}
$_POST = ['csrf_token' => 'irrelevant', 'confirm_delete' => '1'];
$deniedPostResponse = $router->match(new Request('POST', '/wiki/Locked Doc/delete'))();
if ($deniedPostResponse->status() !== 403) {
    $failures[] = '(2) delete 권한이 없는 사용자의 POST는 403이어야 하는데 ' . $deniedPostResponse->status() . '이었다.';
}
if ($documentRepository->get($lockedDoc->id()) === null) {
    $failures[] = '(2) 권한이 없는 POST 시도가 문서를 삭제하면 안 된다.';
}

// (3) 존재하지 않는 문서는 404.
mintwiki_delete_test_login($memberId);
$missingGetResponse = $router->match(new Request('GET', '/wiki/Missing Doc/delete'))();
if ($missingGetResponse->status() !== 404) {
    $failures[] = '(3) 존재하지 않는 문서의 GET은 404여야 한다.';
}
$_POST = ['csrf_token' => 'irrelevant', 'confirm_delete' => '1'];
$missingPostResponse = $router->match(new Request('POST', '/wiki/Missing Doc/delete'))();
if ($missingPostResponse->status() !== 404) {
    $failures[] = '(3) 존재하지 않는 문서의 POST는 404여야 한다.';
}

// (4) CSRF 검증 실패 -> 403, 문서는 그대로 남는다.
mintwiki_delete_test_login($memberId);
$_POST = ['csrf_token' => 'invalid-token', 'confirm_delete' => '1'];
$csrfFailResponse = $router->match(new Request('POST', '/wiki/Open Doc/delete'))();
if ($csrfFailResponse->status() !== 403) {
    $failures[] = '(4) CSRF 검증 실패는 403이어야 하는데 ' . $csrfFailResponse->status() . '이었다.';
}
if ($documentRepository->get($openDoc->id()) === null) {
    $failures[] = '(4) CSRF 검증에 실패하면 문서를 삭제하면 안 된다.';
}

// (5) 확인 체크박스가 없으면 422, 문서는 그대로 남는다.
$validToken = $csrfTokenService->generate();
$_POST = ['csrf_token' => $validToken];
$noConfirmResponse = $router->match(new Request('POST', '/wiki/Open Doc/delete'))();
if ($noConfirmResponse->status() !== 422) {
    $failures[] = '(5) 확인 체크박스가 없으면 422여야 하는데 ' . $noConfirmResponse->status() . '이었다.';
}
if (!str_contains($noConfirmResponse->body(), '동의')) {
    $failures[] = '(5) 확인 체크박스 누락 응답에 안내 메시지가 있어야 한다.';
}
if ($documentRepository->get($openDoc->id()) === null) {
    $failures[] = '(5) 확인 체크박스가 없으면 문서를 삭제하면 안 된다.';
}

// (6) 모든 검증 통과 -> 문서/리비전/토론/acl_rule 삭제 + / 로 302 + 감사 이벤트.
$eventCountBeforeDelete = count($auditQuery->listRecentEvents());
$validToken2 = $csrfTokenService->generate();
$_POST = ['csrf_token' => $validToken2, 'confirm_delete' => '1'];
$deleteResponse = $router->match(new Request('POST', '/wiki/Open Doc/delete'))();

if ($deleteResponse->status() !== 302 || ($deleteResponse->headers()['Location'] ?? null) !== '/') {
    $failures[] = '(6) 삭제 성공은 /로 302여야 하는데 status=' . $deleteResponse->status()
        . ', Location=' . ($deleteResponse->headers()['Location'] ?? 'null') . '이었다.';
}
if ($documentRepository->get($openDoc->id()) !== null) {
    $failures[] = '(6) 삭제 성공 후 문서가 저장소에서 제거되어야 한다.';
}

$eventsAfterDelete = $auditQuery->listRecentEvents();
if (count($eventsAfterDelete) !== $eventCountBeforeDelete + 1) {
    $failures[] = '(6) 삭제 성공 후 감사 이벤트가 정확히 1건 추가되어야 하는데 '
        . (count($eventsAfterDelete) - $eventCountBeforeDelete) . '건 추가되었다.';
} else {
    $deletedEvent = null;
    foreach ($eventsAfterDelete as $candidate) {
        if ($candidate->action() === 'deleted') {
            $deletedEvent = $candidate;
        }
    }
    if ($deletedEvent === null || $deletedEvent->category() !== 'document') {
        $failures[] = '(6) 삭제 감사 이벤트는 category=document, action=deleted여야 한다.';
    } else {
        if ($deletedEvent->entityId() !== $openDoc->id()) {
            $failures[] = '(6) 삭제 감사 이벤트의 entity_id는 삭제된 문서 id여야 한다.';
        }
        if ($deletedEvent->actorId() !== $memberId) {
            $failures[] = '(6) 삭제 감사 이벤트의 actor_id는 로그인한 계정 id여야 한다.';
        }
    }
}

if ($failures !== []) {
    fwrite(STDERR, "GET/POST /wiki/{title}/delete 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET/POST /wiki/{title}/delete 테스트 통과.\n");
exit(0);
