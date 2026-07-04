<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0687에서 `GET /wiki/{title}`과
 * `GET`/`POST /wiki/{title}/edit`에 추가하는 ACL 검사를 확인하는 smoke
 * test. phpunit 없이 `php` CLI만으로 실행된다(0685 DocumentEditRouteTest.php와
 * 동일한 방식) — index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록
 * 로직(ACL 검사 포함)을 Router에 그대로 재구성해 검증한다.
 *
 * 검증 대상(관리자/일반/읽기 전용/익명 네 종류의 subject로 읽기·쓰기
 * 허용·거부를 확인한다):
 * (1) acl_rule이 없는 공개 문서는 익명/읽기 전용/일반/관리자 모두 읽을 수
 *     있다(네임스페이스 기본 정책의 공개 읽기 허용 규칙).
 * (2) 공개 문서 편집은 익명 사용자만 거부되고(네임스페이스 기본 정책의
 *     익명 편집 거부 규칙, GET은 /login으로 302, POST도 /login으로 302),
 *     로그인한 사용자(일반/읽기 전용/관리자)는 허용된다(네임스페이스
 *     기본 정책의 로그인 사용자 편집 허용 규칙).
 * (3) acl_rule로 보호된 문서는 규칙에 문서별 읽기 허용 규칙이 있어
 *     익명/읽기 전용 사용자도 읽을 수 있다.
 * (4) 보호된 문서 편집은 관리자만 허용되고(문서별 허용 규칙), 읽기 전용
 *     사용자는 명시적으로 거부되며(문서별 거부 규칙), 일반 사용자와
 *     익명 사용자는 대상-전체(ALL) 거부 규칙으로 거부된다 — 문서에 규칙이
 *     있으면 네임스페이스 기본값은 전혀 참조하지 않는다는 계약을 함께
 *     확인한다.
 * (5) 편집이 거부되면 POST로도 문서/리비전이 실제로 생성/변경되지 않는다.
 * (6) acl_rule로 전체 읽기 자체를 거부한 문서는 GET /wiki/{title}이
 *     PermissionDeniedPage(403)를 반환한다.
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
use MintWiki\Document\Document;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\InMemoryRepository as DocumentInMemoryRepository;
use MintWiki\Document\Repository as DocumentRepository;
use MintWiki\Document\Service as DocumentService;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Revision\InMemoryRepository as RevisionInMemoryRepository;
use MintWiki\Revision\Repository as RevisionRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\DocumentEditorPage;
use MintWiki\Ui\DocumentViewPage;
use MintWiki\Ui\PermissionDeniedPage;
use MintWiki\User\AccountRepository;

$failures = [];

/**
 * `public/index.php`가 0687에서 등록하는 `GET /wiki/{title}` 핸들러(ACL
 * 검사 포함)와 동일한 등록 로직을 재구성한다(위 파일 docblock 참고).
 */
function mintwiki_register_acl_document_view_route(
    Router $router,
    ?DocumentRepository $documentRepository,
    ?AclPdoRepository $aclRuleRepository,
    AclService $aclService,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter
): void {
    $router->register('GET', '/wiki/{title}', static function (array $params) use (
        $documentRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter
    ): Response {
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

        $documentAcl = $aclRuleRepository?->documentAcl($document->id());
        [$subjectType, $subjectId] = mintwiki_acl_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Read, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            $permissionDeniedPage = new PermissionDeniedPage();

            return Response::html($permissionDeniedPage->render($decision), 403);
        }

        return Response::html($documentViewPage->render($document));
    });
}

/**
 * `public/index.php`가 0687에서 등록하는 `GET`/`POST /wiki/{title}/edit`
 * 핸들러(ACL 검사 포함)와 동일한 등록 로직을 재구성한다(위 파일 docblock
 * 참고).
 */
function mintwiki_acl_test_generate_uuid_v4(): string
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
 * @return array{0: AclSubjectType, 1: ?string}
 */
function mintwiki_acl_test_resolve_subject(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): array
{
    if ($accountRepository !== null) {
        $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
        if ($currentUser !== null) {
            return [AclSubjectType::User, $currentUser->id()];
        }
    }

    return [AclSubjectType::Anonymous, null];
}

function mintwiki_register_acl_document_edit_routes(
    Router $router,
    ?DocumentRepository $documentRepository,
    ?RevisionRepository $revisionRepository,
    ?AclPdoRepository $aclRuleRepository,
    AclService $aclService,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter
): void {
    $router->register('GET', '/wiki/{title}/edit', static function (array $params) use (
        $documentRepository,
        $revisionRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter
    ): Response {
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

        $documentAcl = $document !== null ? $aclRuleRepository?->documentAcl($document->id()) : null;
        [$subjectType, $subjectId] = mintwiki_acl_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Edit, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            if ($subjectType === AclSubjectType::Anonymous) {
                return new Response(302, ['Location' => '/login']);
            }

            $permissionDeniedPage = new PermissionDeniedPage();

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
        $sessionAdapter
    ): Response {
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

        $documentAcl = $existingDocument !== null ? $aclRuleRepository?->documentAcl($existingDocument->id()) : null;
        [$subjectType, $subjectId] = mintwiki_acl_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Edit, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            if ($subjectType === AclSubjectType::Anonymous) {
                return new Response(302, ['Location' => '/login']);
            }

            $permissionDeniedPage = new PermissionDeniedPage();

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
                $parentRevisionId = $document->currentRevisionId();
            }

            $revision = $revisionRepository->create(new Revision(
                mintwiki_acl_test_generate_uuid_v4(),
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
        }

        return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title())]);
    });
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// ACL 규칙(acl_rule/acl_namespace_rule)과 계정(account)은 실제 sqlite
// in-memory DB로 검증한다 — 문서/리비전은 기존 route 테스트와 동일하게
// InMemoryRepository로 충분하다(ACL 검사와 무관한 저장 로직이다).
$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$documentSql = file_get_contents(__DIR__ . '/../../../db/schema/document.sql');
$aclRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_rule.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');

if ($accountSql === false || $documentSql === false || $aclRuleSql === false || $aclNamespaceRuleSql === false) {
    fwrite(STDERR, "db/schema/*.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec($documentSql);
$pdo->exec($accountSql);
$pdo->exec($aclRuleSql);
$pdo->exec($aclNamespaceRuleSql);

$accountRepository = new AccountRepository($pdo);
$adminId = $accountRepository->create('admin', password_hash('irrelevant', PASSWORD_DEFAULT));
$regularId = $accountRepository->create('regular', password_hash('irrelevant', PASSWORD_DEFAULT));
$readonlyId = $accountRepository->create('readonly', password_hash('irrelevant', PASSWORD_DEFAULT));

$documentRepository = new DocumentInMemoryRepository();
$revisionRepository = new RevisionInMemoryRepository();

$publicDocument = $documentRepository->create(new Document('doc-public', 'Public Document'));
$protectedDocument = $documentRepository->create(new Document('doc-protected', 'Protected Document'));
$lockedDocument = $documentRepository->create(new Document('doc-locked', 'Locked Document'));

// 보호된 문서(doc-protected): 모두 읽기 허용, admin만 편집 허용, readonly는
// 명시적으로 편집 거부, 나머지(ALL)는 편집 거부. 문서에 규칙이 있으므로
// AclService는 네임스페이스 기본값을 전혀 참조하지 않는다.
$insertRule = $pdo->prepare(
    'INSERT INTO acl_rule (id, document_id, subject_type, subject_id, permission, effect, expires_at, sort_order) '
    . 'VALUES (:id, :document_id, :subject_type, :subject_id, :permission, :effect, NULL, :sort_order)'
);
$insertRule->execute(['id' => 'rule-protected-read-all', 'document_id' => 'doc-protected', 'subject_type' => 'all', 'subject_id' => null, 'permission' => 'read', 'effect' => 'allow', 'sort_order' => 0]);
$insertRule->execute(['id' => 'rule-protected-edit-admin', 'document_id' => 'doc-protected', 'subject_type' => 'user', 'subject_id' => $adminId, 'permission' => 'edit', 'effect' => 'allow', 'sort_order' => 1]);
$insertRule->execute(['id' => 'rule-protected-edit-readonly-deny', 'document_id' => 'doc-protected', 'subject_type' => 'user', 'subject_id' => $readonlyId, 'permission' => 'edit', 'effect' => 'deny', 'sort_order' => 2]);
$insertRule->execute(['id' => 'rule-protected-edit-all-deny', 'document_id' => 'doc-protected', 'subject_type' => 'all', 'subject_id' => null, 'permission' => 'edit', 'effect' => 'deny', 'sort_order' => 3]);

// 잠긴 문서(doc-locked): 모두 읽기 거부 — GET /wiki/{title}의 read 거부
// 경로(PermissionDeniedPage, 403)를 확인한다.
$insertRule->execute(['id' => 'rule-locked-read-all-deny', 'document_id' => 'doc-locked', 'subject_type' => 'all', 'subject_id' => null, 'permission' => 'read', 'effect' => 'deny', 'sort_order' => 0]);

$aclRuleRepository = new AclPdoRepository($pdo);
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
$aclService = new AclService($namespaceAclDefaults);

$sessionAdapter = new PhpSessionAdapter();
$csrfTokenService = new CsrfTokenService();

$router = new Router();
mintwiki_register_acl_document_view_route($router, $documentRepository, $aclRuleRepository, $aclService, $accountRepository, $sessionAdapter);
mintwiki_register_acl_document_edit_routes($router, $documentRepository, $revisionRepository, $aclRuleRepository, $aclService, $accountRepository, $sessionAdapter);

/**
 * 세션에 로그인 사용자를 설정하거나(익명이면 null) 초기화한다.
 */
function mintwiki_acl_test_login(?string $accountId): void
{
    $_SESSION = [];
    if ($accountId !== null) {
        $_SESSION[SessionUserResolver::SESSION_KEY] = $accountId;
    }
}

// (1) 공개 문서(acl_rule 없음)는 익명/읽기 전용/일반/관리자 모두 읽을 수 있다.
foreach (['anonymous' => null, 'readonly' => $readonlyId, 'regular' => $regularId, 'admin' => $adminId] as $label => $accountId) {
    mintwiki_acl_test_login($accountId);
    $response = $router->match(new Request('GET', '/wiki/Public Document'))();
    if ($response->status() !== 200) {
        $failures[] = "(1) {$label}의 공개 문서 읽기는 200이어야 하는데 {$response->status()}이었다.";
    }
}

// (2) 공개 문서 편집: 익명은 거부(GET/POST 모두 /login으로 302), 로그인한
// 사용자(일반/읽기 전용/관리자)는 허용된다(네임스페이스 기본값).
mintwiki_acl_test_login(null);
$anonEditGet = $router->match(new Request('GET', '/wiki/Public Document/edit'))();
if ($anonEditGet->status() !== 302 || ($anonEditGet->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(2) 익명 사용자의 공개 문서 편집 GET은 /login으로 302여야 하는데 그렇지 않았다(status=' . $anonEditGet->status() . ').';
}

$validToken = $csrfTokenService->generate();
$_POST = ['title' => 'Public Document', 'source' => 'Anonymous edit attempt', 'csrf_token' => $validToken];
$anonEditPost = $router->match(new Request('POST', '/wiki/Public Document/edit'))();
if ($anonEditPost->status() !== 302 || ($anonEditPost->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(2) 익명 사용자의 공개 문서 편집 POST는 /login으로 302여야 하는데 그렇지 않았다(status=' . $anonEditPost->status() . ').';
}
if ($documentRepository->get('doc-public')->currentRevisionId() !== null) {
    $failures[] = '(2) 익명 사용자의 편집 POST가 거부되었으므로 공개 문서에 리비전이 생기면 안 된다.';
}

foreach (['readonly' => $readonlyId, 'regular' => $regularId, 'admin' => $adminId] as $label => $accountId) {
    mintwiki_acl_test_login($accountId);
    $editGetResponse = $router->match(new Request('GET', '/wiki/Public Document/edit'))();
    if ($editGetResponse->status() !== 200) {
        $failures[] = "(2) {$label}의 공개 문서 편집 GET은 200이어야 하는데 {$editGetResponse->status()}이었다.";
    }
}

// 일반 사용자가 공개 문서를 실제로 편집할 수 있어야 한다(성공 시 302 + 리비전 생성).
mintwiki_acl_test_login($regularId);
$validToken2 = $csrfTokenService->generate();
$_POST = ['title' => 'Public Document', 'source' => 'Edited by regular user', 'csrf_token' => $validToken2];
$regularEditPost = $router->match(new Request('POST', '/wiki/Public Document/edit'))();
if ($regularEditPost->status() !== 302) {
    $failures[] = '(2) 일반 사용자의 공개 문서 편집 POST는 302를 반환해야 하는데 ' . $regularEditPost->status() . '이었다.';
}
if (count($revisionRepository->listByDocumentId('doc-public')) !== 1) {
    $failures[] = '(2) 일반 사용자의 편집 성공 이후 공개 문서에 리비전이 1개 있어야 한다.';
}

// (3) 보호된 문서는 문서별 읽기 허용 규칙 덕분에 익명/읽기 전용 사용자도 읽을 수 있다.
foreach (['anonymous' => null, 'readonly' => $readonlyId] as $label => $accountId) {
    mintwiki_acl_test_login($accountId);
    $protectedReadResponse = $router->match(new Request('GET', '/wiki/Protected Document'))();
    if ($protectedReadResponse->status() !== 200) {
        $failures[] = "(3) {$label}의 보호된 문서 읽기는 200이어야 하는데 {$protectedReadResponse->status()}이었다.";
    }
}

// (4)/(5) 보호된 문서 편집: admin만 허용, readonly/regular/anonymous는 거부되고
// 아무것도 저장되지 않는다.
mintwiki_acl_test_login($adminId);
$adminEditGetResponse = $router->match(new Request('GET', '/wiki/Protected Document/edit'))();
if ($adminEditGetResponse->status() !== 200) {
    $failures[] = '(4) 관리자의 보호된 문서 편집 GET은 200이어야 하는데 ' . $adminEditGetResponse->status() . '이었다.';
}
$adminToken = $csrfTokenService->generate();
$_POST = ['title' => 'Protected Document', 'source' => 'Edited by admin', 'csrf_token' => $adminToken];
$adminEditPostResponse = $router->match(new Request('POST', '/wiki/Protected Document/edit'))();
if ($adminEditPostResponse->status() !== 302) {
    $failures[] = '(4) 관리자의 보호된 문서 편집 POST는 302여야 하는데 ' . $adminEditPostResponse->status() . '이었다.';
}
if (count($revisionRepository->listByDocumentId('doc-protected')) !== 1) {
    $failures[] = '(4) 관리자의 편집 성공 이후 보호된 문서에 리비전이 1개 있어야 한다.';
}

foreach (['readonly' => $readonlyId, 'regular' => $regularId] as $label => $accountId) {
    mintwiki_acl_test_login($accountId);

    $deniedGetResponse = $router->match(new Request('GET', '/wiki/Protected Document/edit'))();
    if ($deniedGetResponse->status() !== 403) {
        $failures[] = "(4) {$label}의 보호된 문서 편집 GET은 403이어야 하는데 {$deniedGetResponse->status()}이었다.";
    }
    if (!str_contains($deniedGetResponse->body(), '권한 없음')) {
        $failures[] = "(4) {$label}의 보호된 문서 편집 거부 응답은 PermissionDeniedPage를 보여줘야 한다.";
    }

    $token = $csrfTokenService->generate();
    $_POST = ['title' => 'Protected Document', 'source' => "Edit attempt by {$label}", 'csrf_token' => $token];
    $deniedPostResponse = $router->match(new Request('POST', '/wiki/Protected Document/edit'))();
    if ($deniedPostResponse->status() !== 403) {
        $failures[] = "(5) {$label}의 보호된 문서 편집 POST는 403이어야 하는데 {$deniedPostResponse->status()}이었다.";
    }
}

// 익명 사용자의 보호된 문서 편집은 /login으로 302여야 한다.
mintwiki_acl_test_login(null);
$anonProtectedGetResponse = $router->match(new Request('GET', '/wiki/Protected Document/edit'))();
if ($anonProtectedGetResponse->status() !== 302 || ($anonProtectedGetResponse->headers()['Location'] ?? null) !== '/login') {
    $failures[] = '(4) 익명 사용자의 보호된 문서 편집 GET은 /login으로 302여야 한다.';
}

// (5) 위 거부들 이후에도 보호된 문서의 리비전은 admin이 만든 1개 그대로여야 한다.
if (count($revisionRepository->listByDocumentId('doc-protected')) !== 1) {
    $failures[] = '(5) 거부된 편집 시도들로 인해 보호된 문서에 원치 않는 리비전이 추가되면 안 된다.';
}

// (6) 잠긴 문서(전체 읽기 거부)는 GET /wiki/{title}이 403(PermissionDeniedPage)이어야 한다.
foreach (['anonymous' => null, 'admin' => $adminId] as $label => $accountId) {
    mintwiki_acl_test_login($accountId);
    $lockedReadResponse = $router->match(new Request('GET', '/wiki/Locked Document'))();
    if ($lockedReadResponse->status() !== 403) {
        $failures[] = "(6) {$label}의 잠긴 문서 읽기는 403이어야 하는데 {$lockedReadResponse->status()}이었다.";
    }
    if (!str_contains($lockedReadResponse->body(), 'read')) {
        $failures[] = "(6) 잠긴 문서 읽기 거부 응답은 read 권한 정보를 포함해야 한다.";
    }
}

if ($failures !== []) {
    fwrite(STDERR, "GET /wiki/{title}, GET/POST /wiki/{title}/edit ACL 적용 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /wiki/{title}, GET/POST /wiki/{title}/edit ACL 적용 테스트 통과.\n");
exit(0);
