<?php

declare(strict_types=1);

/**
 * `public/index.php`가 태스크 0710에서 등록하는
 * `GET /wiki/{title}/history`와 `GET /wiki/{title}/diff`를 확인하는 smoke
 * test. phpunit 없이 `php` CLI만으로 실행된다(0687 `DocumentAclEnforcementTest.php`와
 * 동일한 방식) — index.php는 재사용 가능한 모듈이 아니므로, 동일한 등록
 * 로직(ACL 검사 포함)을 Router에 그대로 재구성해 검증한다. 문서/리비전은
 * 실제 sqlite PDO + `Document\PdoRepository`/`Revision\PdoRepository`로
 * 만든다 — history 화면에 필요한 실제 `created_at` 값을 얻기 위함이다.
 *
 * 검증 대상:
 * (1) history route가 문서의 리비전을 시간 내림차순으로 렌더링하고, 각
 *     행에 작성자/시각/요약/보기 링크(부모가 있으면)가 있는지.
 * (2) diff route가 두 리비전 source의 실제 줄 단위 차이를 렌더링하는지.
 * (3) 읽기 권한이 없는 문서는 두 route 모두 403(PermissionDeniedPage)을
 *     반환하는지.
 * (4) 존재하지 않는 문서는 두 route 모두 404를 반환하는지.
 * (5) diff route에 존재하지 않는/다른 문서 소속의 리비전 id를 주면 404를
 *     반환하는지.
 * (6) 리비전이 0개/1개인 경계 상태를 history route가 안전하게 렌더링하는지.
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
use MintWiki\Document\PdoRepository as DocumentPdoRepository;
use MintWiki\Document\Repository as DocumentRepository;
use MintWiki\Document\Service as DocumentService;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Revision\PdoRepository as RevisionPdoRepository;
use MintWiki\Revision\Repository as RevisionRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\Ui\DocumentDiffPage;
use MintWiki\Ui\DocumentHistoryPage;
use MintWiki\Ui\ErrorPage;
use MintWiki\Ui\PermissionDeniedPage;
use MintWiki\User\AccountRepository;

$failures = [];

/**
 * @return array{0: AclSubjectType, 1: ?string}
 */
function mintwiki_history_diff_test_resolve_subject(?AccountRepository $accountRepository, PhpSessionAdapter $sessionAdapter): array
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
 * `public/index.php`가 0710에서 등록하는 `GET /wiki/{title}/history`,
 * `GET /wiki/{title}/diff` 핸들러와 동일한 등록 로직을 재구성한다(위 파일
 * docblock 참고).
 */
function mintwiki_register_history_diff_routes(
    Router $router,
    ?DocumentRepository $documentRepository,
    ?RevisionRepository $revisionRepository,
    ?AclPdoRepository $aclRuleRepository,
    AclService $aclService,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter
): void {
    $router->register('GET', '/wiki/{title}/history', static function (array $params) use (
        $documentRepository,
        $revisionRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter
    ): Response {
        $requestedTitle = rawurldecode($params['title'] ?? '');

        if ($documentRepository === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/history'), 404);
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/history'), 404);
        }

        $documentAcl = $aclRuleRepository?->documentAcl($document->id());
        [$subjectType, $subjectId] = mintwiki_history_diff_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Read, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            return Response::html((new PermissionDeniedPage())->render($decision), 403);
        }

        $revisions = $revisionRepository !== null
            ? array_reverse($revisionRepository->listByDocumentId($document->id()))
            : [];

        return Response::html((new DocumentHistoryPage())->render($document, $revisions));
    });

    $router->register('GET', '/wiki/{title}/diff', static function (array $params) use (
        $documentRepository,
        $revisionRepository,
        $aclRuleRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter
    ): Response {
        $requestedTitle = rawurldecode($params['title'] ?? '');

        if ($documentRepository === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/diff'), 404);
        }

        $documentService = new DocumentService($documentRepository);

        try {
            $document = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $document = null;
        }

        if ($document === null) {
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/diff'), 404);
        }

        $documentAcl = $aclRuleRepository?->documentAcl($document->id());
        [$subjectType, $subjectId] = mintwiki_history_diff_test_resolve_subject($accountRepository, $sessionAdapter);
        $decision = $aclService->check(AclPermission::Read, $subjectType, $subjectId, $documentAcl);

        if ($decision->isDenied()) {
            return Response::html((new PermissionDeniedPage())->render($decision), 403);
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
            return Response::html((new ErrorPage())->renderNotFound('/wiki/' . $requestedTitle . '/diff'), 404);
        }

        return Response::html((new DocumentDiffPage())->render($document, $fromRevision, $toRevision));
    });
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
$_SESSION = [];
$_GET = [];

// 실제 sqlite in-memory DB로 document/revision/acl을 검증한다(위 파일
// docblock 참고) — history 화면에 필요한 진짜 created_at 값을 얻기 위함이다.
$documentSql = file_get_contents(__DIR__ . '/../../../db/schema/document.sql');
$revisionSql = file_get_contents(__DIR__ . '/../../../db/schema/revision.sql');
$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$aclRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_rule.sql');
$aclNamespaceRuleSql = file_get_contents(__DIR__ . '/../../../db/schema/acl_namespace_rule.sql');

if ($documentSql === false || $revisionSql === false || $accountSql === false || $aclRuleSql === false || $aclNamespaceRuleSql === false) {
    fwrite(STDERR, "db/schema/*.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec($documentSql);
$pdo->exec($revisionSql);
$pdo->exec($accountSql);
$pdo->exec($aclRuleSql);
$pdo->exec($aclNamespaceRuleSql);

$documentRepository = new DocumentPdoRepository($pdo);
$revisionRepository = new RevisionPdoRepository($pdo);
$aclRuleRepository = new AclPdoRepository($pdo);
$namespaceAclDefaults = new NamespaceAclDefaults();
$namespaceAclDefaults->register(NamespaceAclDefaults::DEFAULT_NAMESPACE, DefaultPolicy::defaultRules());
$aclService = new AclService($namespaceAclDefaults);
$sessionAdapter = new PhpSessionAdapter();

$documentService = new DocumentService($documentRepository);

$router = new Router();
mintwiki_register_history_diff_routes($router, $documentRepository, $revisionRepository, $aclRuleRepository, $aclService, null, $sessionAdapter);

// 문서 하나에 리비전 3개를 순서대로 생성한다(공개 문서, acl_rule 없음).
$document = $documentService->create('History Diff Test Doc');
$rev1 = $revisionRepository->create(new Revision('rev-1', $document->id(), "첫째 줄\n둘째 줄", 'user-1', '최초 작성', null));
$rev2 = $revisionRepository->create(new Revision('rev-2', $document->id(), "첫째 줄\n수정된 둘째 줄", 'user-2', '오타 수정', 'rev-1'));
$rev3 = $revisionRepository->create(new Revision('rev-3', $document->id(), "첫째 줄\n수정된 둘째 줄\n셋째 줄 추가", 'user-1', '내용 추가', 'rev-2'));

// (1) history route: 시간 내림차순 렌더링 + 작성자/시각/요약/보기 링크.
$historyResponse = $router->match(new Request('GET', '/wiki/History Diff Test Doc/history'))();
if ($historyResponse->status() !== 200) {
    $failures[] = "(1) history route는 200이어야 하는데 {$historyResponse->status()}이었다.";
}
$historyBody = $historyResponse->body();

$rev3Pos = strpos($historyBody, 'ID: rev-3');
$rev2Pos = strpos($historyBody, 'ID: rev-2');
$rev1Pos = strpos($historyBody, 'ID: rev-1');
if ($rev3Pos === false || $rev2Pos === false || $rev1Pos === false || !($rev3Pos < $rev2Pos && $rev2Pos < $rev1Pos)) {
    $failures[] = '(1) history route는 리비전을 시간 내림차순(최신순)으로 표시해야 한다.';
}

if (!str_contains($historyBody, '작성자: user-1') || !str_contains($historyBody, '작성자: user-2')) {
    $failures[] = '(1) history route가 각 리비전의 작성자를 표시해야 한다.';
}

if (!str_contains($historyBody, '요약: 최초 작성') || !str_contains($historyBody, '요약: 오타 수정')) {
    $failures[] = '(1) history route가 각 리비전의 편집 요약을 표시해야 한다.';
}

if (str_contains($historyBody, '시각: -')) {
    $failures[] = '(1) 실제 DB에서 읽은 리비전은 생성 시각이 있어야 한다("시각: -"가 아니어야 한다).';
}

if (!str_contains($historyBody, '최초 버전')) {
    $failures[] = '(1) 부모가 없는 첫 리비전은 "최초 버전"으로 표시해야 한다.';
}

if (!str_contains($historyBody, 'diff?from=rev-1&amp;to=rev-2') || !str_contains($historyBody, 'diff?from=rev-2&amp;to=rev-3')) {
    $failures[] = '(1) 부모가 있는 리비전은 직전 리비전과 비교하는 "보기" 링크를 가져야 한다.';
}

// (2) diff route: 실제 줄 단위 차이 렌더링.
$_GET = ['from' => 'rev-1', 'to' => 'rev-3'];
$diffResponse = $router->match(new Request('GET', '/wiki/History Diff Test Doc/diff'))();
if ($diffResponse->status() !== 200) {
    $failures[] = "(2) diff route는 200이어야 하는데 {$diffResponse->status()}이었다.";
}
$diffBody = $diffResponse->body();
if (!str_contains($diffBody, 'From: rev-1') || !str_contains($diffBody, 'To: rev-3')) {
    $failures[] = '(2) diff route가 From/To 리비전 id를 표시해야 한다.';
}
if (!str_contains($diffBody, '<li class="document-diff__line--removed">- 둘째 줄</li>')) {
    $failures[] = '(2) diff route가 삭제된 줄을 표시해야 한다.';
}
if (!str_contains($diffBody, '<li class="document-diff__line--added">+ 수정된 둘째 줄</li>')) {
    $failures[] = '(2) diff route가 추가된 줄을 표시해야 한다.';
}
if (!str_contains($diffBody, '<li class="document-diff__line--added">+ 셋째 줄 추가</li>')) {
    $failures[] = '(2) diff route가 마지막에 추가된 줄을 표시해야 한다.';
}
if (!str_contains($diffBody, '<li class="document-diff__line--unchanged">  첫째 줄</li>')) {
    $failures[] = '(2) diff route가 바뀌지 않은 줄은 unchanged로 표시해야 한다.';
}
$_GET = [];

// (3) 읽기 권한이 없는 문서: 두 route 모두 403.
$lockedDocument = $documentService->create('Locked History Doc');
$revisionRepository->create(new Revision('rev-locked-1', $lockedDocument->id(), '잠긴 내용', 'user-1', '최초', null));
$insertRule = $pdo->prepare(
    'INSERT INTO acl_rule (id, document_id, subject_type, subject_id, permission, effect, expires_at, sort_order) '
    . 'VALUES (:id, :document_id, :subject_type, :subject_id, :permission, :effect, NULL, :sort_order)'
);
$insertRule->execute(['id' => 'rule-locked-read-deny', 'document_id' => $lockedDocument->id(), 'subject_type' => 'all', 'subject_id' => null, 'permission' => 'read', 'effect' => 'deny', 'sort_order' => 0]);

$lockedHistoryResponse = $router->match(new Request('GET', '/wiki/Locked History Doc/history'))();
if ($lockedHistoryResponse->status() !== 403) {
    $failures[] = "(3) 읽기 거부된 문서의 history route는 403이어야 하는데 {$lockedHistoryResponse->status()}이었다.";
}

$_GET = ['from' => 'rev-locked-1', 'to' => 'rev-locked-1'];
$lockedDiffResponse = $router->match(new Request('GET', '/wiki/Locked History Doc/diff'))();
if ($lockedDiffResponse->status() !== 403) {
    $failures[] = "(3) 읽기 거부된 문서의 diff route는 403이어야 하는데 {$lockedDiffResponse->status()}이었다.";
}
$_GET = [];

// (4) 존재하지 않는 문서: 두 route 모두 404.
$missingHistoryResponse = $router->match(new Request('GET', '/wiki/No Such Document/history'))();
if ($missingHistoryResponse->status() !== 404) {
    $failures[] = "(4) 존재하지 않는 문서의 history route는 404여야 하는데 {$missingHistoryResponse->status()}이었다.";
}
$missingDiffResponse = $router->match(new Request('GET', '/wiki/No Such Document/diff'))();
if ($missingDiffResponse->status() !== 404) {
    $failures[] = "(4) 존재하지 않는 문서의 diff route는 404여야 하는데 {$missingDiffResponse->status()}이었다.";
}

// (5) diff route에 존재하지 않거나 다른 문서 소속인 리비전 id를 주면 404.
$_GET = ['from' => 'rev-does-not-exist', 'to' => 'rev-3'];
$badDiffResponse = $router->match(new Request('GET', '/wiki/History Diff Test Doc/diff'))();
if ($badDiffResponse->status() !== 404) {
    $failures[] = "(5) 존재하지 않는 리비전 id로 diff route를 호출하면 404여야 하는데 {$badDiffResponse->status()}이었다.";
}

$_GET = ['from' => 'rev-locked-1', 'to' => 'rev-3'];
$crossDocDiffResponse = $router->match(new Request('GET', '/wiki/History Diff Test Doc/diff'))();
if ($crossDocDiffResponse->status() !== 404) {
    $failures[] = "(5) 다른 문서 소속 리비전 id를 섞은 diff route는 404여야 하는데 {$crossDocDiffResponse->status()}이었다.";
}
$_GET = [];

// (6) 리비전이 0개/1개인 경계 상태.
$emptyDocument = $documentService->create('Empty History Doc');
$emptyHistoryResponse = $router->match(new Request('GET', '/wiki/Empty History Doc/history'))();
if ($emptyHistoryResponse->status() !== 200) {
    $failures[] = "(6) 리비전이 없는 문서의 history route는 200이어야 하는데 {$emptyHistoryResponse->status()}이었다.";
}
if (!str_contains($emptyHistoryResponse->body(), '리비전이 없습니다.')) {
    $failures[] = '(6) 리비전이 없는 문서는 "리비전이 없습니다."를 표시해야 한다.';
}

$singleDocument = $documentService->create('Single Revision Doc');
$revisionRepository->create(new Revision('rev-single-1', $singleDocument->id(), '단일 리비전 내용', 'user-1', '최초 작성', null));
$singleHistoryResponse = $router->match(new Request('GET', '/wiki/Single Revision Doc/history'))();
if ($singleHistoryResponse->status() !== 200) {
    $failures[] = "(6) 리비전이 1개인 문서의 history route는 200이어야 하는데 {$singleHistoryResponse->status()}이었다.";
}
$singleHistoryBody = $singleHistoryResponse->body();
if (str_contains($singleHistoryBody, '<form') || str_contains($singleHistoryBody, 'type="radio"')) {
    $failures[] = '(6) 리비전이 1개뿐이면 비교 form/라디오 버튼이 없어야 한다.';
}
if (!str_contains($singleHistoryBody, '최초 버전')) {
    $failures[] = '(6) 리비전이 1개뿐이면(부모 없음) "최초 버전"으로 표시해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "GET /wiki/{title}/history, GET /wiki/{title}/diff 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "GET /wiki/{title}/history, GET /wiki/{title}/diff 테스트 통과.\n");
exit(0);
