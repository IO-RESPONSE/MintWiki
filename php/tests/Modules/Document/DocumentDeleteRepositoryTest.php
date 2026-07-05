<?php

declare(strict_types=1);

/**
 * `MintWiki\Document\Repository::delete()`(태스크 0715)의 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다(다른 Modules/Document
 * 테스트와 동일한 방식).
 *
 * 검증 대상:
 * (1) `InMemoryRepository::delete()`는 document를 제거하고, 없는 id에는
 *     `NotFoundError`를 던진다.
 * (2) `Document\Service::delete()`는 저장소의 `delete()`에 위임한다.
 * (3) `PdoRepository::delete()`는 하드 삭제를 수행하며, `revision`/
 *     `discussion_thread`/`discussion_comment`/`acl_rule`처럼 삭제할 문서의
 *     id를 FK로 참조하는 행을 먼저 정리해 `PRAGMA foreign_keys = ON` 상태의
 *     sqlite에서도 FK 위반 없이 문서를 지운다(설계 근거는
 *     `Document\PdoRepository` 클래스 docblock 참고).
 * (4) `PdoRepository::delete()`는 다른 문서의 리비전/스레드/규칙은 건드리지
 *     않는다.
 * (5) `PdoRepository::delete()`는 없는 id에 대해 `NotFoundError`를 던지고
 *     아무것도 지우지 않는다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\Comment;
use MintWiki\Discussion\PdoRepository as DiscussionPdoRepository;
use MintWiki\Discussion\Thread;
use MintWiki\Document\Document;
use MintWiki\Document\InMemoryRepository;
use MintWiki\Document\NotFoundError;
use MintWiki\Document\PdoRepository;
use MintWiki\Document\Service;
use MintWiki\Revision\PdoRepository as RevisionPdoRepository;
use MintWiki\Revision\Revision;

$failures = [];

// ------------------------------------------------------------------
// (1)/(2) InMemoryRepository + Service.
// ------------------------------------------------------------------
$inMemoryRepository = new InMemoryRepository();
$service = new Service($inMemoryRepository);

$document = $inMemoryRepository->create(new Document('doc-1', 'Deletable Document'));
$service->delete($document->id());

if ($inMemoryRepository->get('doc-1') !== null) {
    $failures[] = '(1) Service::delete()는 InMemoryRepository에서 document를 제거해야 한다.';
}
if ($inMemoryRepository->getByNormalizedTitle('Deletable Document') !== null) {
    $failures[] = '(1) 삭제 후에는 normalizedTitle로도 조회되지 않아야 한다(재생성 허용).';
}

try {
    $service->delete('doc-missing');
    $failures[] = '(1) delete()는 없는 id에 대해 NotFoundError를 던져야 한다.';
} catch (NotFoundError $error) {
    // 정상 경로.
}

// 삭제 후 같은 제목으로 재생성할 수 있어야 한다(정규화 제목 UNIQUE 제약이
// 남아있지 않음을 함께 확인).
$recreated = $inMemoryRepository->create(new Document('doc-2', 'Deletable Document'));
if ($recreated->id() !== 'doc-2') {
    $failures[] = '(1) 삭제된 문서와 같은 제목으로 재생성할 수 있어야 한다.';
}

// ------------------------------------------------------------------
// (3)/(4)/(5) PdoRepository — 실제 sqlite in-memory PDO, FK 강제.
// ------------------------------------------------------------------
$documentSql = file_get_contents(__DIR__ . '/../../../../db/schema/document.sql');
$revisionSql = file_get_contents(__DIR__ . '/../../../../db/schema/revision.sql');
$aclRuleSql = file_get_contents(__DIR__ . '/../../../../db/schema/acl_rule.sql');
$discussionThreadSql = file_get_contents(__DIR__ . '/../../../../db/schema/discussion_thread.sql');
$discussionCommentSql = file_get_contents(__DIR__ . '/../../../../db/schema/discussion_comment.sql');

if (
    $documentSql === false || $revisionSql === false || $aclRuleSql === false
    || $discussionThreadSql === false || $discussionCommentSql === false
) {
    fwrite(STDERR, "db/schema/*.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec('PRAGMA foreign_keys = ON');
$pdo->exec($documentSql);
$pdo->exec($revisionSql);
$pdo->exec($aclRuleSql);
$pdo->exec($discussionThreadSql);
$pdo->exec($discussionCommentSql);

$documentRepository = new PdoRepository($pdo);
$revisionRepository = new RevisionPdoRepository($pdo);
$discussionRepository = new DiscussionPdoRepository($pdo);

$targetDocument = $documentRepository->create(new Document('target-doc', 'Target Document'));
$otherDocument = $documentRepository->create(new Document('other-doc', 'Other Document'));

$targetRevision = $revisionRepository->create(new Revision('rev-target-1', $targetDocument->id(), 'source', 'author', 'summary'));
$documentRepository->update(new Document($targetDocument->id(), $targetDocument->title(), $targetRevision->id()));

$otherRevision = $revisionRepository->create(new Revision('rev-other-1', $otherDocument->id(), 'other source', 'author', 'summary'));
$documentRepository->update(new Document($otherDocument->id(), $otherDocument->title(), $otherRevision->id()));

$thread = $discussionRepository->createThread(new Thread('thread-1', $targetDocument->id(), 'Thread Title', 'alice', new DateTimeImmutable('now')));
$discussionRepository->createComment(new Comment('comment-1', $thread->id(), 'body', 'alice', new DateTimeImmutable('now')));

$otherThread = $discussionRepository->createThread(new Thread('thread-other-1', $otherDocument->id(), 'Other Thread', 'bob', new DateTimeImmutable('now')));

$insertRule = $pdo->prepare(
    'INSERT INTO acl_rule (id, document_id, subject_type, subject_id, permission, effect, expires_at, sort_order) '
    . 'VALUES (:id, :document_id, :subject_type, :subject_id, :permission, :effect, NULL, :sort_order)'
);
$insertRule->execute(['id' => 'rule-target-1', 'document_id' => $targetDocument->id(), 'subject_type' => 'all', 'subject_id' => null, 'permission' => 'read', 'effect' => 'allow', 'sort_order' => 0]);
$insertRule->execute(['id' => 'rule-other-1', 'document_id' => $otherDocument->id(), 'subject_type' => 'all', 'subject_id' => null, 'permission' => 'read', 'effect' => 'allow', 'sort_order' => 0]);

// (3) 삭제 실행 — FK 위반 없이 성공해야 한다.
try {
    $documentRepository->delete($targetDocument->id());
} catch (\Throwable $exception) {
    $failures[] = '(3) delete()는 FK 위반 없이 성공해야 하는데 예외가 발생했다: ' . $exception->getMessage();
}

if ($documentRepository->get($targetDocument->id()) !== null) {
    $failures[] = '(3) delete() 이후 document 행이 남아 있으면 안 된다.';
}
if ($revisionRepository->get($targetRevision->id()) !== null) {
    $failures[] = '(3) delete() 이후 대상 문서의 revision이 남아 있으면 안 된다.';
}
if ($discussionRepository->getThread($thread->id()) !== null) {
    $failures[] = '(3) delete() 이후 대상 문서의 discussion_thread가 남아 있으면 안 된다.';
}
if ($discussionRepository->listCommentsByThreadId($thread->id()) !== []) {
    $failures[] = '(3) delete() 이후 대상 스레드의 discussion_comment가 남아 있으면 안 된다.';
}
$remainingRules = $pdo->query("SELECT COUNT(*) FROM acl_rule WHERE document_id = 'target-doc'")->fetchColumn();
if ((int) $remainingRules !== 0) {
    $failures[] = '(3) delete() 이후 대상 문서의 acl_rule이 남아 있으면 안 된다.';
}

// (4) 다른 문서의 데이터는 영향받지 않아야 한다.
if ($documentRepository->get($otherDocument->id()) === null) {
    $failures[] = '(4) 다른 문서는 삭제되면 안 된다.';
}
if ($revisionRepository->get($otherRevision->id()) === null) {
    $failures[] = '(4) 다른 문서의 revision은 삭제되면 안 된다.';
}
if ($discussionRepository->getThread($otherThread->id()) === null) {
    $failures[] = '(4) 다른 문서의 discussion_thread는 삭제되면 안 된다.';
}
$otherRemainingRules = $pdo->query("SELECT COUNT(*) FROM acl_rule WHERE document_id = 'other-doc'")->fetchColumn();
if ((int) $otherRemainingRules !== 1) {
    $failures[] = '(4) 다른 문서의 acl_rule은 삭제되면 안 된다.';
}

// (5) 없는 id는 NotFoundError, 아무것도 지우지 않는다.
try {
    $documentRepository->delete('missing-doc');
    $failures[] = '(5) delete()는 없는 id에 대해 NotFoundError를 던져야 한다.';
} catch (NotFoundError $error) {
    // 정상 경로.
}
if ($documentRepository->get($otherDocument->id()) === null) {
    $failures[] = '(5) 실패한 delete() 시도가 다른 문서에 영향을 주면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Document 삭제 저장소 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Document 삭제 저장소 테스트 통과.\n");
exit(0);
