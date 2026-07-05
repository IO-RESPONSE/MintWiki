<?php

declare(strict_types=1);

/**
 * `MintWiki\Discussion\PdoRepository`(태스크 0711)의 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다(`Acl\PdoRepository`
 * 테스트 - php/tests/Modules/Acl/PdoRepositoryGrantNamespacePermissionTest.php
 * - 와 동일한 방식). 실제 DB 없이 sqlite in-memory에
 * `db/schema/document.sql`/`discussion_thread.sql`/`discussion_comment.sql`을
 * 적용해 검증한다 — 라우트 배선(0712) 없이도 이식성 정책(복합 인덱스
 * 정렬 tiebreaker, UTC 타임스탬프 문자열)이 SQLite에서 지켜지는지가 핵심
 * 관심사다.
 *
 * 검증 대상:
 * (1) createThread()가 저장한 값 그대로 discussion_thread에 행을 남기고,
 *     getThread()로 그대로 조회된다.
 * (2) listThreadsByDocumentId()는 해당 문서의 스레드만, created_at
 *     오름차순 + id 2차 정렬(같은 시각 tiebreaker)로 반환한다.
 * (3) createComment()/listCommentsByThreadId()도 (1)/(2)와 동일한 계약을
 *     따른다.
 * (4) 빈 제목/본문 등 도메인 오류(Empty*Error)는 Thread/Comment 생성자
 *     단계에서 발생해 PdoRepository까지 도달하지 않는다 — 어떤 행도
 *     삽입되지 않는다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\Comment;
use MintWiki\Discussion\EmptyThreadTitleError;
use MintWiki\Discussion\PdoRepository;
use MintWiki\Discussion\Thread;
use MintWiki\Document\PdoRepository as DocumentPdoRepository;

$failures = [];

$documentSql = file_get_contents(__DIR__ . '/../../../db/schema/document.sql');
$discussionThreadSql = file_get_contents(__DIR__ . '/../../../db/schema/discussion_thread.sql');
$discussionCommentSql = file_get_contents(__DIR__ . '/../../../db/schema/discussion_comment.sql');

if ($documentSql === false || $discussionThreadSql === false || $discussionCommentSql === false) {
    fwrite(STDERR, "db/schema/*.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connection->exec($documentSql);
$connection->exec($discussionThreadSql);
$connection->exec($discussionCommentSql);

$documentRepository = new DocumentPdoRepository($connection);
$documentOne = $documentRepository->create(new \MintWiki\Document\Document('doc-1', 'First Document'));
$documentTwo = $documentRepository->create(new \MintWiki\Document\Document('doc-2', 'Second Document'));

$repository = new PdoRepository($connection);

// (1) createThread()/getThread() 왕복
$createdAt = new \DateTimeImmutable('2026-01-01T10:00:00+00:00');
$thread = new Thread('thread-1', $documentOne->id(), '  첫   스레드  ', 'user-1', $createdAt);
$repository->createThread($thread);

$rows = $connection->query('SELECT * FROM discussion_thread WHERE id = \'thread-1\'')->fetchAll(PDO::FETCH_ASSOC);
if (count($rows) !== 1) {
    $failures[] = '(1) createThread() 이후 discussion_thread에 행이 정확히 1개 있어야 하는데 ' . count($rows) . '개였다.';
} else {
    $row = $rows[0];
    if ($row['document_id'] !== $documentOne->id()) {
        $failures[] = '(1) 저장된 document_id가 전달한 값과 달랐다.';
    }
    if ($row['title'] !== '첫 스레드') {
        $failures[] = '(1) 저장된 title이 Thread의 정규화 결과와 달랐다.';
    }
    if ($row['status'] !== 'open') {
        $failures[] = '(1) 저장된 status는 Thread 생성자의 기본값 open이어야 한다.';
    }
    if ($row['closed_at'] !== null || $row['paused_at'] !== null) {
        $failures[] = '(1) 새로 만든 스레드는 closed_at/paused_at이 비어있어야 한다.';
    }
}

$fetchedThread = $repository->getThread('thread-1');
if (
    $fetchedThread === null
    || $fetchedThread->id() !== 'thread-1'
    || $fetchedThread->title() !== '첫 스레드'
    || $fetchedThread->createdBy() !== 'user-1'
    || $fetchedThread->status() !== 'open'
    || $fetchedThread->createdAt()->format('Y-m-d H:i:s') !== $createdAt->format('Y-m-d H:i:s')
) {
    $failures[] = '(1) getThread()는 createThread()로 저장한 값을 그대로 조회해야 한다.';
}
if ($repository->getThread('missing-thread') !== null) {
    $failures[] = '(1) getThread()는 없는 id에 대해 null을 반환해야 한다.';
}

// (2) listThreadsByDocumentId(): 문서 분리 + 같은 시각 tiebreaker(id 오름차순)
$repository->createThread(new Thread('thread-3', $documentOne->id(), '같은 시각 스레드 B', 'user-2', $createdAt));
$repository->createThread(new Thread('thread-2', $documentOne->id(), '같은 시각 스레드 A', 'user-2', $createdAt));
$repository->createThread(new Thread('thread-4', $documentTwo->id(), '다른 문서 스레드', 'user-1', $createdAt));

$threadsForDocumentOne = $repository->listThreadsByDocumentId($documentOne->id());
$threadIds = array_map(fn (Thread $thread): string => $thread->id(), $threadsForDocumentOne);
if ($threadIds !== ['thread-1', 'thread-2', 'thread-3']) {
    $failures[] = '(2) listThreadsByDocumentId()는 문서별로 걸러내고, 같은 created_at은 id 오름차순으로 정렬해야 하는데 ['
        . implode(', ', $threadIds) . ']였다.';
}
$threadsForDocumentTwo = $repository->listThreadsByDocumentId($documentTwo->id());
if (count($threadsForDocumentTwo) !== 1 || $threadsForDocumentTwo[0]->id() !== 'thread-4') {
    $failures[] = '(2) listThreadsByDocumentId()는 해당 문서의 스레드만 반환해야 한다.';
}
if ($repository->listThreadsByDocumentId('missing-doc') !== []) {
    $failures[] = '(2) listThreadsByDocumentId()는 스레드가 없는 문서에 대해 빈 배열을 반환해야 한다.';
}

// (3) createComment()/listCommentsByThreadId(): 스레드 분리 + tiebreaker
$comment = new Comment('comment-1', 'thread-1', '첫 댓글', 'user-2', $createdAt);
$repository->createComment($comment);

$commentRows = $connection->query('SELECT * FROM discussion_comment WHERE id = \'comment-1\'')->fetchAll(PDO::FETCH_ASSOC);
if (count($commentRows) !== 1) {
    $failures[] = '(3) createComment() 이후 discussion_comment에 행이 정확히 1개 있어야 하는데 ' . count($commentRows) . '개였다.';
} else {
    $commentRow = $commentRows[0];
    if ($commentRow['thread_id'] !== 'thread-1' || $commentRow['body'] !== '첫 댓글' || (int) $commentRow['is_hidden'] !== 0) {
        $failures[] = '(3) 저장된 댓글의 컬럼 값이 전달한 값과 달랐다.';
    }
}

$repository->createComment(new Comment('comment-3', 'thread-1', '같은 시각 댓글 B', 'user-1', $createdAt));
$repository->createComment(new Comment('comment-2', 'thread-1', '같은 시각 댓글 A', 'user-1', $createdAt));
$repository->createComment(new Comment('comment-4', 'thread-2', '다른 스레드 댓글', 'user-1', $createdAt));

$commentsForThreadOne = $repository->listCommentsByThreadId('thread-1');
$commentIds = array_map(fn (Comment $comment): string => $comment->id(), $commentsForThreadOne);
if ($commentIds !== ['comment-1', 'comment-2', 'comment-3']) {
    $failures[] = '(3) listCommentsByThreadId()는 스레드별로 걸러내고, 같은 created_at은 id 오름차순으로 정렬해야 하는데 ['
        . implode(', ', $commentIds) . ']였다.';
}
$commentsForThreadTwo = $repository->listCommentsByThreadId('thread-2');
if (count($commentsForThreadTwo) !== 1 || $commentsForThreadTwo[0]->id() !== 'comment-4') {
    $failures[] = '(3) listCommentsByThreadId()는 해당 스레드의 댓글만 반환해야 한다.';
}
if ($repository->listCommentsByThreadId('missing-thread') !== []) {
    $failures[] = '(3) listCommentsByThreadId()는 댓글이 없는 스레드에 대해 빈 배열을 반환해야 한다.';
}

// (4) 도메인 오류는 Thread/Comment 생성자 단계에서 발생해 저장소까지 도달하지 않는다.
try {
    new Thread('thread-invalid', $documentOne->id(), '   ', 'user-1', $createdAt);
    $failures[] = '(4) 공백만 있는 title로 Thread를 생성하면 EmptyThreadTitleError를 던져야 한다.';
} catch (EmptyThreadTitleError) {
    // 정상 경로 — 아무 것도 하지 않는다.
}
$rowsAfterInvalidThread = $connection->query('SELECT COUNT(*) FROM discussion_thread WHERE id = \'thread-invalid\'')->fetchColumn();
if ((int) $rowsAfterInvalidThread !== 0) {
    $failures[] = '(4) 생성자에서 실패한 Thread는 discussion_thread에 어떤 행도 남기면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "PdoRepository 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "PdoRepository 테스트 통과.\n");
exit(0);
