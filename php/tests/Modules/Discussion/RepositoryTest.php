<?php

declare(strict_types=1);

/**
 * MintWiki\Discussion\Repository 포트의 시그니처와 계약을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0405 Revision/RepositoryTest.php와
 * 동일한 방식).
 *
 * 이 테스트는 실제 저장소 동작이 아니라 (1) 인터페이스가 계약대로 구현
 * 가능한지 — 익명 클래스로 구현해 본다 — 와 (2) listThreadsByDocumentId/
 * listCommentsByThreadId가 생성 순서를 유지하는지만 확인한다. 실제 구현체
 * (InMemoryRepository/PdoRepository)의 상세 동작은 각각의 전용 테스트가
 * 검증한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\Comment;
use MintWiki\Discussion\Repository;
use MintWiki\Discussion\Thread;

$failures = [];

if (!interface_exists(Repository::class)) {
    $failures[] = 'MintWiki\\Discussion\\Repository는 interface여야 한다.';
}

$repository = new class implements Repository {
    /** @var array<string, Thread> */
    private array $threads = [];

    /** @var array<string, string[]> */
    private array $threadIdsByDocumentId = [];

    /** @var array<string, Comment> */
    private array $comments = [];

    /** @var array<string, string[]> */
    private array $commentIdsByThreadId = [];

    public function createThread(Thread $thread): Thread
    {
        $this->threads[$thread->id()] = $thread;
        $this->threadIdsByDocumentId[$thread->documentId()][] = $thread->id();
        return $thread;
    }

    public function getThread(string $id): ?Thread
    {
        return $this->threads[$id] ?? null;
    }

    public function listThreadsByDocumentId(string $documentId): array
    {
        $ids = $this->threadIdsByDocumentId[$documentId] ?? [];
        return array_map(fn (string $id): Thread => $this->threads[$id], $ids);
    }

    public function createComment(Comment $comment): Comment
    {
        $this->comments[$comment->id()] = $comment;
        $this->commentIdsByThreadId[$comment->threadId()][] = $comment->id();
        return $comment;
    }

    public function listCommentsByThreadId(string $threadId): array
    {
        $ids = $this->commentIdsByThreadId[$threadId] ?? [];
        return array_map(fn (string $id): Comment => $this->comments[$id], $ids);
    }
};

$createdAt = new \DateTimeImmutable('2026-01-01T00:00:00+00:00');

$firstThread = $repository->createThread(new Thread('thread-1', 'doc-1', 'First thread', 'user-1', $createdAt));
if ($firstThread->id() !== 'thread-1') {
    $failures[] = 'createThread()는 저장한 스레드를 반환해야 한다.';
}
if ($repository->getThread('thread-1') === null) {
    $failures[] = 'getThread()는 createThread()로 저장한 스레드를 조회해야 한다.';
}
if ($repository->getThread('missing') !== null) {
    $failures[] = 'getThread()는 없는 id에 대해 null을 반환해야 한다.';
}

$secondThread = $repository->createThread(new Thread('thread-2', 'doc-1', 'Second thread', 'user-2', $createdAt));
$repository->createThread(new Thread('thread-3', 'doc-2', 'Other document thread', 'user-1', $createdAt));

$byDocument = $repository->listThreadsByDocumentId('doc-1');
if (count($byDocument) !== 2) {
    $failures[] = 'listThreadsByDocumentId()는 해당 문서의 스레드만 반환해야 한다.';
}
if (($byDocument[0] ?? null) !== $firstThread || ($byDocument[1] ?? null) !== $secondThread) {
    $failures[] = 'listThreadsByDocumentId()는 생성 순서대로 스레드를 반환해야 한다.';
}
if ($repository->listThreadsByDocumentId('missing-doc') !== []) {
    $failures[] = 'listThreadsByDocumentId()는 스레드가 없는 문서에 대해 빈 배열을 반환해야 한다.';
}

$firstComment = $repository->createComment(new Comment('comment-1', 'thread-1', 'First comment', 'user-1', $createdAt));
if ($firstComment->id() !== 'comment-1') {
    $failures[] = 'createComment()는 저장한 댓글을 반환해야 한다.';
}

$secondComment = $repository->createComment(new Comment('comment-2', 'thread-1', 'Second comment', 'user-2', $createdAt));
$repository->createComment(new Comment('comment-3', 'thread-2', 'Other thread comment', 'user-1', $createdAt));

$byThread = $repository->listCommentsByThreadId('thread-1');
if (count($byThread) !== 2) {
    $failures[] = 'listCommentsByThreadId()는 해당 스레드의 댓글만 반환해야 한다.';
}
if (($byThread[0] ?? null) !== $firstComment || ($byThread[1] ?? null) !== $secondComment) {
    $failures[] = 'listCommentsByThreadId()는 생성 순서대로 댓글을 반환해야 한다.';
}
if ($repository->listCommentsByThreadId('missing-thread') !== []) {
    $failures[] = 'listCommentsByThreadId()는 댓글이 없는 스레드에 대해 빈 배열을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Repository 포트 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Repository 포트 테스트 통과.\n");
exit(0);
