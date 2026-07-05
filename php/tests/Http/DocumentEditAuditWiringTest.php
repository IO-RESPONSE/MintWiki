<?php

declare(strict_types=1);

/**
 * `public/index.php`가 `POST /wiki/{title}/edit`(태스크 0685, 0687)에서
 * 문서 생성/편집 시 감사 이벤트를 남기는지(태스크 0714) 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다(0698 AdminAuditRouteTest.php와 동일한
 * 방식) — index.php는 재사용 가능한 모듈이 아니므로, 감사 기록과 직접 관련된
 * 핵심 로직만 동일하게 재구성해 검증한다.
 *
 * 검증 대상:
 * (1) 로그인한 사용자가 새 문서를 저장하면 module=document, action=created
 *     감사 이벤트가 기록되고, actorId/entity_id는 로그인 계정 id/문서 id다.
 * (2) 같은 문서를 다시 저장(편집)하면 module=document, action=updated 감사
 *     이벤트가 추가로 기록되고, related_entity_id는 새로 생성된 리비전 id다.
 * (3) 익명 사용자가 저장을 시도하면 ACL 거부로 `/login`으로 302되고, 감사
 *     이벤트가 기록되지 않는다.
 * (4) 주입된 `AuditRecorder`가 예외를 던져도 문서 저장(302 리다이렉트)은
 *     그대로 성공한다 — 방어적 try/catch.
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
use MintWiki\Acl\SubjectType as AclSubjectType;
use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\AuditRecorder;
use MintWiki\Audit\PdoAuditRecorder;
use MintWiki\Audit\RecentAuditEventsQuery;
use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\EmptyTitleError;
use MintWiki\Document\PdoRepository as DocumentPdoRepository;
use MintWiki\Document\Service as DocumentService;
use MintWiki\Http\Request;
use MintWiki\Http\Response;
use MintWiki\Http\Router;
use MintWiki\Revision\PdoRepository as RevisionPdoRepository;
use MintWiki\Revision\Revision;
use MintWiki\Security\CsrfTokenService;
use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\User\AccountRepository;

/**
 * UUID v4 문자열을 생성한다 (리비전 id 발급용, `public/index.php`
 * mintwiki_generate_uuid_v4()와 동일).
 */
function mintwiki_document_edit_audit_generate_uuid_v4(): string
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
 * `public/index.php`의 `POST /wiki/{title}/edit` 핸들러 중 감사 기록과 직접
 * 관련된 부분(ACL 검사 -> 문서/리비전 저장 -> 감사 이벤트 기록)만 재구성한다
 * (위 파일 docblock 참고). 렌더링/CSRF/유효성 검사는 0685/0708에서 이미
 * 검증되었으므로 여기서는 생략한다.
 */
function mintwiki_register_document_edit_audit_route(
    Router $router,
    DocumentService $documentService,
    RevisionPdoRepository $revisionRepository,
    AclService $aclService,
    ?AccountRepository $accountRepository,
    PhpSessionAdapter $sessionAdapter,
    AuditRecorder $auditRecorder
): void {
    $router->register('POST', '/wiki/{title}/edit', static function (array $params) use (
        $documentService,
        $revisionRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter,
        $auditRecorder
    ): Response {
        $requestedTitle = rawurldecode($params['title'] ?? '');
        $titleInput = is_string($_POST['title'] ?? null) ? $_POST['title'] : '';
        $sourceInput = is_string($_POST['source'] ?? null) ? $_POST['source'] : '';

        try {
            $existingDocument = $documentService->getByTitle($requestedTitle);
        } catch (EmptyTitleError) {
            $existingDocument = null;
        }
        $isNew = $existingDocument === null;

        $subjectType = AclSubjectType::Anonymous;
        $subjectId = null;
        if ($accountRepository !== null) {
            $currentUser = (new SessionUserResolver($sessionAdapter, $accountRepository))->resolve();
            if ($currentUser !== null) {
                $subjectType = AclSubjectType::User;
                $subjectId = $currentUser->id();
            }
        }

        $decision = $aclService->check(\MintWiki\Acl\Permission::Edit, $subjectType, $subjectId);
        if ($decision->isDenied()) {
            if ($subjectType === AclSubjectType::Anonymous) {
                return new Response(302, ['Location' => '/login']);
            }

            return new Response(403, []);
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
                mintwiki_document_edit_audit_generate_uuid_v4(),
                $document->id(),
                $sourceInput,
                '',
                '',
                $parentRevisionId
            ));

            $document = $documentService->update(new Document($document->id(), $document->title(), $revision->id()));
        } catch (EmptyTitleError | DuplicateNormalizedTitleError) {
            return new Response(422, []);
        }

        try {
            $auditRecorder->record(new AuditEvent(
                id: mintwiki_document_edit_audit_generate_uuid_v4(),
                module: 'document',
                action: $isNew ? 'created' : 'updated',
                occurredAt: new \DateTimeImmutable('now'),
                actorId: $subjectType === AclSubjectType::Anonymous ? 'anonymous' : $subjectId,
                metadata: ['entity_id' => $document->id(), 'related_entity_id' => $revision->id()]
            ));
        } catch (\Throwable $exception) {
            \error_log('Audit recording failed: ' . $exception->getMessage());
        }

        return new Response(302, ['Location' => '/wiki/' . rawurlencode($document->title())]);
    });
}

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];

$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
$documentSql = file_get_contents(__DIR__ . '/../../../db/schema/document.sql');
$revisionSql = file_get_contents(__DIR__ . '/../../../db/schema/revision.sql');
$auditEventSql = file_get_contents(__DIR__ . '/../../../db/schema/audit_event.sql');
if ($accountSql === false || $documentSql === false || $revisionSql === false || $auditEventSql === false) {
    fwrite(STDERR, "필요한 schema 파일을 읽을 수 없습니다.\n");
    exit(1);
}

try {
    $pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec($accountSql);
    $pdo->exec($documentSql);
    $pdo->exec($revisionSql);
    $pdo->exec($auditEventSql);

    $accountRepository = new AccountRepository($pdo);
    $userId = $accountRepository->create('writer', password_hash('irrelevant', PASSWORD_DEFAULT));

    $documentRepository = new DocumentPdoRepository($pdo);
    $documentService = new DocumentService($documentRepository);
    $revisionRepository = new RevisionPdoRepository($pdo);

    $aclService = new AclService(DefaultPolicy::buildDefaultNamespaceAclDefaults());
    $auditRecorder = new PdoAuditRecorder($pdo);
    $auditQuery = new RecentAuditEventsQuery($pdo);
    $sessionAdapter = new PhpSessionAdapter();

    // ------------------------------------------------------------------
    // (1) 로그인한 사용자가 새 문서를 저장 -> module=document, action=created.
    // ------------------------------------------------------------------
    $_SESSION = [SessionUserResolver::SESSION_KEY => $userId];
    $router = new Router();
    mintwiki_register_document_edit_audit_route(
        $router,
        $documentService,
        $revisionRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter,
        $auditRecorder
    );

    $_POST = ['title' => 'Audit Wired Document', 'source' => 'first body'];
    $createResponse = $router->match(new Request('POST', '/wiki/Audit Wired Document/edit'))();

    if ($createResponse->status() !== 302) {
        $failures[] = '(1) 로그인한 사용자의 새 문서 저장은 302를 반환해야 하는데 ' . $createResponse->status() . '이었다.';
    }

    $createdDocument = $documentRepository->getByNormalizedTitle('Audit Wired Document');
    if ($createdDocument === null) {
        $failures[] = '(1) 새 문서가 저장소에 생성되어 있어야 한다.';
    }

    $eventsAfterCreate = $auditQuery->listRecentEvents();
    if (count($eventsAfterCreate) !== 1) {
        $failures[] = '(1) 문서 생성 이후 감사 이벤트가 1건 기록되어야 하는데 ' . count($eventsAfterCreate) . '건이었다.';
    } else {
        $createdEvent = $eventsAfterCreate[0];
        if ($createdEvent->category() !== 'document' || $createdEvent->action() !== 'created') {
            $failures[] = '(1) 문서 생성 이벤트는 category=document, action=created여야 한다.';
        }
        if ($createdEvent->actorId() !== $userId) {
            $failures[] = '(1) 문서 생성 이벤트의 actor_id는 로그인한 계정 id여야 한다.';
        }
        if ($createdDocument !== null && $createdEvent->entityId() !== $createdDocument->id()) {
            $failures[] = '(1) 문서 생성 이벤트의 entity_id는 생성된 문서 id여야 한다.';
        }
    }

    // ------------------------------------------------------------------
    // (2) 같은 문서를 다시 저장(편집) -> module=document, action=updated,
    //     related_entity_id는 새 리비전 id.
    // ------------------------------------------------------------------
    $_POST = ['title' => 'Audit Wired Document', 'source' => 'second body'];
    $editResponse = $router->match(new Request('POST', '/wiki/Audit Wired Document/edit'))();

    if ($editResponse->status() !== 302) {
        $failures[] = '(2) 기존 문서 편집 저장은 302를 반환해야 하는데 ' . $editResponse->status() . '이었다.';
    }

    $revisionsAfterEdit = $revisionRepository->listByDocumentId($createdDocument->id());
    if (count($revisionsAfterEdit) !== 2) {
        $failures[] = '(2) 편집 이후 리비전은 2개여야 하는데 ' . count($revisionsAfterEdit) . '개였다.';
    }
    // listByDocumentId()는 동일 초(created_at 정밀도)에 생성된 리비전을 id로
    // 2차 정렬하므로 배열 순서로 "새 리비전"을 특정할 수 없다 — 문서의
    // currentRevisionId가 가리키는 실제 최신 리비전 id를 대신 사용한다.
    $newRevisionId = $documentRepository->get($createdDocument->id())?->currentRevisionId();

    // created/updated 이벤트가 같은 초(occurred_at 정밀도)에 기록될 수 있어
    // 정렬 순서(내림차순)만으로 최신 이벤트를 특정하지 않고, action으로 찾는다.
    $eventsAfterEdit = $auditQuery->listRecentEvents();
    if (count($eventsAfterEdit) !== 2) {
        $failures[] = '(2) 문서 편집 이후 감사 이벤트는 총 2건이어야 하는데 ' . count($eventsAfterEdit) . '건이었다.';
    } else {
        $updatedEvent = null;
        foreach ($eventsAfterEdit as $candidate) {
            if ($candidate->action() === 'updated') {
                $updatedEvent = $candidate;
            }
        }
        if ($updatedEvent === null || $updatedEvent->category() !== 'document') {
            $failures[] = '(2) 문서 편집 이벤트는 category=document, action=updated여야 한다.';
        } elseif ($newRevisionId !== null && $updatedEvent->relatedEntityId() !== $newRevisionId) {
            $failures[] = '(2) 문서 편집 이벤트의 related_entity_id는 새로 생성된 리비전 id여야 한다.';
        }
    }

    // ------------------------------------------------------------------
    // (3) 익명 사용자는 /login으로 302되고, 감사 이벤트가 추가되지 않아야 한다.
    // ------------------------------------------------------------------
    $_SESSION = [];
    $countBeforeAnonymous = count($auditQuery->listRecentEvents());
    $_POST = ['title' => 'Anonymous Attempt', 'source' => 'should not save'];
    $anonymousResponse = $router->match(new Request('POST', '/wiki/Anonymous Attempt/edit'))();

    if ($anonymousResponse->status() !== 302 || ($anonymousResponse->headers()['Location'] ?? null) !== '/login') {
        $failures[] = '(3) 익명 사용자의 저장 시도는 /login으로 302여야 한다.';
    }
    if ($documentRepository->getByNormalizedTitle('Anonymous Attempt') !== null) {
        $failures[] = '(3) 익명 사용자의 저장 시도는 문서를 생성하면 안 된다.';
    }
    if (count($auditQuery->listRecentEvents()) !== $countBeforeAnonymous) {
        $failures[] = '(3) 익명 사용자의 저장 시도는 감사 이벤트를 추가로 기록하면 안 된다.';
    }

    // ------------------------------------------------------------------
    // (4) 감사 기록이 예외를 던져도 문서 저장(302)은 그대로 성공해야 한다.
    // ------------------------------------------------------------------
    $_SESSION = [SessionUserResolver::SESSION_KEY => $userId];
    $failingAuditRecorder = new class implements AuditRecorder {
        public function record(AuditEvent $event): void
        {
            throw new \Exception('Audit recording failure');
        }
    };
    $failingRouter = new Router();
    mintwiki_register_document_edit_audit_route(
        $failingRouter,
        $documentService,
        $revisionRepository,
        $aclService,
        $accountRepository,
        $sessionAdapter,
        $failingAuditRecorder
    );

    $_POST = ['title' => 'Resilient Document', 'source' => 'saved despite audit failure'];
    $resilientResponse = $failingRouter->match(new Request('POST', '/wiki/Resilient Document/edit'))();

    if ($resilientResponse->status() !== 302) {
        $failures[] = '(4) 감사 기록이 실패해도 문서 저장은 302를 반환해야 하는데 ' . $resilientResponse->status() . '이었다.';
    }
    if ($documentRepository->getByNormalizedTitle('Resilient Document') === null) {
        $failures[] = '(4) 감사 기록이 실패해도 문서는 저장소에 저장되어 있어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '문서 편집 감사 wiring 테스트 실패: ' . $e->getMessage();
}

if ($failures !== []) {
    fwrite(STDERR, "POST /wiki/{title}/edit 감사 로그 wiring 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "POST /wiki/{title}/edit 감사 로그 wiring 테스트 통과.\n");
exit(0);
