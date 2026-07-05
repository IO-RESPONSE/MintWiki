<?php

declare(strict_types=1);

/**
 * MintWiki\Discussion\Service의 생성/조회 계약을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0403 Document/ServiceTest.php와
 * 동일한 방식). `InMemoryRepository`를 실제로 사용해 검증한다.
 *
 * close/reopen/pause_thread, hide_comment 등은 이 태스크(0711) 범위 밖이라
 * 다루지 않는다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\EmptyCommentBodyError;
use MintWiki\Discussion\EmptyCommentCreatedByError;
use MintWiki\Discussion\EmptyThreadCreatedByError;
use MintWiki\Discussion\EmptyThreadTitleError;
use MintWiki\Discussion\InMemoryRepository;
use MintWiki\Discussion\Service;
use MintWiki\Discussion\ThreadState;

$failures = [];

$service = new Service(new InMemoryRepository());

$thread = $service->createThread('doc-1', '  첫 번째   토론  ', 'user-1');

if ($thread->documentId() !== 'doc-1') {
    $failures[] = 'createThread()는 전달한 documentId를 가진 스레드를 반환해야 한다.';
}
if ($thread->title() !== '첫 번째 토론') {
    $failures[] = 'createThread()가 반환한 스레드는 Thread의 제목 정규화를 그대로 반영해야 한다.';
}
if ($thread->createdBy() !== 'user-1') {
    $failures[] = 'createThread()는 전달한 createdBy를 가진 스레드를 반환해야 한다.';
}
if ($thread->id() === '') {
    $failures[] = 'createThread()는 비어있지 않은 id를 발급해야 한다.';
}
if ($thread->status() !== ThreadState::Open->value) {
    $failures[] = 'createThread()로 만든 스레드의 초기 상태는 ThreadState::Open이어야 한다.';
}

$fetchedThread = $service->getThread($thread->id());
if ($fetchedThread === null || $fetchedThread->id() !== $thread->id()) {
    $failures[] = 'getThread()는 createThread()로 만든 스레드를 id로 조회해야 한다.';
}
if ($service->getThread('missing-thread-id') !== null) {
    $failures[] = 'getThread()는 없는 id에 대해 null을 반환해야 한다.';
}

$otherThread = $service->createThread('doc-1', '두 번째 토론', 'user-2');
$unrelatedThread = $service->createThread('doc-2', '다른 문서 토론', 'user-1');

if ($thread->id() === $otherThread->id()) {
    $failures[] = 'createThread()는 호출마다 서로 다른 id를 발급해야 한다.';
}

$threadsForDoc1 = $service->listThreadsByDocumentId('doc-1');
if (count($threadsForDoc1) !== 2 || $threadsForDoc1[0]->id() !== $thread->id() || $threadsForDoc1[1]->id() !== $otherThread->id()) {
    $failures[] = 'listThreadsByDocumentId()는 doc-1의 스레드만 생성 순서대로 반환해야 한다.';
}
if ($service->listThreadsByDocumentId('missing-doc') !== []) {
    $failures[] = 'listThreadsByDocumentId()는 스레드가 없는 문서에 대해 빈 배열을 반환해야 한다.';
}

try {
    $service->createThread('doc-1', '   ', 'user-1');
    $failures[] = 'createThread()는 공백만 있는 title에 대해 EmptyThreadTitleError를 던져야 한다.';
} catch (EmptyThreadTitleError) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

try {
    $service->createThread('doc-1', '제목', '   ');
    $failures[] = 'createThread()는 공백만 있는 createdBy에 대해 EmptyThreadCreatedByError를 던져야 한다.';
} catch (EmptyThreadCreatedByError) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

$comment = $service->addComment($thread->id(), '첫 댓글', 'user-2');
if ($comment->threadId() !== $thread->id()) {
    $failures[] = 'addComment()는 전달한 threadId를 가진 댓글을 반환해야 한다.';
}
if ($comment->body() !== '첫 댓글') {
    $failures[] = 'addComment()는 전달한 body를 가진 댓글을 반환해야 한다.';
}
if ($comment->id() === '') {
    $failures[] = 'addComment()는 비어있지 않은 id를 발급해야 한다.';
}

$secondComment = $service->addComment($thread->id(), '두 번째 댓글', 'user-1');
$otherThreadComment = $service->addComment($otherThread->id(), '다른 스레드 댓글', 'user-1');

$commentsForThread = $service->listCommentsByThreadId($thread->id());
if (
    count($commentsForThread) !== 2
    || $commentsForThread[0]->id() !== $comment->id()
    || $commentsForThread[1]->id() !== $secondComment->id()
) {
    $failures[] = 'listCommentsByThreadId()는 해당 스레드의 댓글만 생성 순서대로 반환해야 한다.';
}
if ($service->listCommentsByThreadId('missing-thread') !== []) {
    $failures[] = 'listCommentsByThreadId()는 댓글이 없는 스레드에 대해 빈 배열을 반환해야 한다.';
}

try {
    $service->addComment($thread->id(), '   ', 'user-1');
    $failures[] = 'addComment()는 공백만 있는 body에 대해 EmptyCommentBodyError를 던져야 한다.';
} catch (EmptyCommentBodyError) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

try {
    $service->addComment($thread->id(), '본문', '   ');
    $failures[] = 'addComment()는 공백만 있는 createdBy에 대해 EmptyCommentCreatedByError를 던져야 한다.';
} catch (EmptyCommentCreatedByError) {
    // 정상 경로 — 아무 것도 하지 않는다.
}

if ($unrelatedThread->documentId() !== 'doc-2' || $otherThreadComment->threadId() !== $otherThread->id()) {
    $failures[] = '서로 다른 문서/스레드에 걸친 생성이 서로 섞이면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Service 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Service 테스트 통과.\n");
exit(0);
