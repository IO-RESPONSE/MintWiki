<?php

declare(strict_types=1);

/**
 * `MintWiki\Discussion\InMemoryRepository`의 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다(0436 Revision/InMemoryRepositoryTest.php와
 * 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\Comment;
use MintWiki\Discussion\InMemoryRepository;
use MintWiki\Discussion\Repository;
use MintWiki\Discussion\Thread;

$failures = [];

if (!(new InMemoryRepository()) instanceof Repository) {
    $failures[] = 'InMemoryRepository는 Repository 인터페이스를 구현해야 한다.';
}

$createdAt = new \DateTimeImmutable('2026-01-01T00:00:00+00:00');

// 스레드 생성/단건 조회
$repository = new InMemoryRepository();
$thread = new Thread('thread-1', 'doc-1', 'Hello thread', 'user-1', $createdAt);
$createdThread = $repository->createThread($thread);
if (
    $createdThread->id() !== 'thread-1'
    || $createdThread->documentId() !== 'doc-1'
    || $createdThread->title() !== 'Hello thread'
    || $createdThread->createdBy() !== 'user-1'
) {
    $failures[] = 'createThread()는 저장한 스레드를 그대로 반환해야 한다.';
}
$fetchedThread = $repository->getThread('thread-1');
if ($fetchedThread === null || $fetchedThread->id() !== 'thread-1') {
    $failures[] = 'getThread()는 createThread()로 저장한 스레드를 id로 조회해야 한다.';
}
if ($repository->getThread('nonexistent') !== null) {
    $failures[] = 'getThread()는 없는 id에 대해 null을 반환해야 한다.';
}

// 문서별 스레드 목록 (생성 순서, 문서 분리)
$repository = new InMemoryRepository();
$thread1Doc1 = $repository->createThread(new Thread('thread1', 'doc1', 'doc1 thread1', 'user1', $createdAt));
$thread1Doc2 = $repository->createThread(new Thread('thread2', 'doc2', 'doc2 thread1', 'user1', $createdAt));
$thread2Doc1 = $repository->createThread(new Thread('thread3', 'doc1', 'doc1 thread2', 'user2', $createdAt));

$doc1Threads = $repository->listThreadsByDocumentId('doc1');
$doc2Threads = $repository->listThreadsByDocumentId('doc2');
if (count($doc1Threads) !== 2 || $doc1Threads[0] !== $thread1Doc1 || $doc1Threads[1] !== $thread2Doc1) {
    $failures[] = 'listThreadsByDocumentId()는 doc1의 스레드만 생성 순서대로 반환해야 한다.';
}
if (count($doc2Threads) !== 1 || $doc2Threads[0] !== $thread1Doc2) {
    $failures[] = 'listThreadsByDocumentId()는 doc2의 스레드만 생성 순서대로 반환해야 한다.';
}
if ($repository->listThreadsByDocumentId('nonexistent-doc') !== []) {
    $failures[] = 'listThreadsByDocumentId()는 없는 문서에 대해 빈 배열을 반환해야 한다.';
}

// 댓글 추가/스레드별 댓글 목록 (생성 순서, 스레드 분리)
$repository = new InMemoryRepository();
$comment1Thread1 = $repository->createComment(new Comment('c1', 'thread1', 'first', 'user1', $createdAt));
$comment1Thread2 = $repository->createComment(new Comment('c2', 'thread2', 'other thread comment', 'user1', $createdAt));
$comment2Thread1 = $repository->createComment(new Comment('c3', 'thread1', 'second', 'user2', $createdAt));

$thread1Comments = $repository->listCommentsByThreadId('thread1');
$thread2Comments = $repository->listCommentsByThreadId('thread2');
if (count($thread1Comments) !== 2 || $thread1Comments[0] !== $comment1Thread1 || $thread1Comments[1] !== $comment2Thread1) {
    $failures[] = 'listCommentsByThreadId()는 thread1의 댓글만 생성 순서대로 반환해야 한다.';
}
if (count($thread2Comments) !== 1 || $thread2Comments[0] !== $comment1Thread2) {
    $failures[] = 'listCommentsByThreadId()는 thread2의 댓글만 생성 순서대로 반환해야 한다.';
}
if ($repository->listCommentsByThreadId('nonexistent-thread') !== []) {
    $failures[] = 'listCommentsByThreadId()는 없는 스레드에 대해 빈 배열을 반환해야 한다.';
}

// 삽입 순서 보존 (5개)
$repository = new InMemoryRepository();
$expectedIds = [];
for ($i = 0; $i < 5; $i++) {
    $id = "thread{$i}";
    $repository->createThread(new Thread($id, 'doc1', "Thread {$i}", 'user1', $createdAt));
    $expectedIds[] = $id;
}
$listed = $repository->listThreadsByDocumentId('doc1');
$actualIds = array_map(fn (Thread $thread): string => $thread->id(), $listed);
if ($actualIds !== $expectedIds) {
    $failures[] = 'InMemoryRepository는 삽입 순서대로 스레드를 나열해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "InMemoryRepository 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "InMemoryRepository 테스트 통과.\n");
exit(0);
