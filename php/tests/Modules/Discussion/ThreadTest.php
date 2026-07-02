<?php

declare(strict_types=1);

/**
 * MintWiki\Discussion\Thread 도메인 모델의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0409 UserTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\EmptyThreadCreatedByError;
use MintWiki\Discussion\EmptyThreadDocumentIdError;
use MintWiki\Discussion\EmptyThreadIdError;
use MintWiki\Discussion\EmptyThreadTitleError;
use MintWiki\Discussion\Thread;

$failures = [];

$createdAt = new \DateTimeImmutable('2026-01-01T00:00:00+00:00');
$thread = new Thread('thread1', 'doc1', '  제목   입니다  ', 'user1', $createdAt);

if ($thread->id() !== 'thread1') {
    $failures[] = 'id()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($thread->documentId() !== 'doc1') {
    $failures[] = 'documentId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($thread->title() !== '제목 입니다') {
    $failures[] = 'title()은 주변 공백을 제거하고 내부 공백을 단일 공백으로 축소해야 한다.';
}
if ($thread->createdBy() !== 'user1') {
    $failures[] = 'createdBy()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($thread->createdAt() !== $createdAt) {
    $failures[] = 'createdAt()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($thread->status() !== 'open') {
    $failures[] = 'status() 기본값은 open이어야 한다.';
}
if ($thread->closedAt() !== null) {
    $failures[] = 'closedAt() 기본값은 null이어야 한다.';
}
if ($thread->pausedAt() !== null) {
    $failures[] = 'pausedAt() 기본값은 null이어야 한다.';
}
if ($thread->isOpen() !== true) {
    $failures[] = '기본 상태에서 isOpen()은 true여야 한다.';
}
if ($thread->isPaused() !== false) {
    $failures[] = '기본 상태에서 isPaused()는 false여야 한다.';
}

$closedAt = new \DateTimeImmutable('2026-01-02T00:00:00+00:00');
$thread->close($closedAt);

if ($thread->status() !== 'closed') {
    $failures[] = 'close() 이후 status()는 closed여야 한다.';
}
if ($thread->closedAt() !== $closedAt) {
    $failures[] = 'close() 이후 closedAt()은 전달한 시각을 반환해야 한다.';
}
if ($thread->isOpen() !== false) {
    $failures[] = 'close() 이후 isOpen()은 false여야 한다.';
}

$thread->reopen();

if ($thread->status() !== 'open') {
    $failures[] = 'reopen() 이후 status()는 open이어야 한다.';
}
if ($thread->closedAt() !== null) {
    $failures[] = 'reopen()은 closedAt()을 null로 되돌려야 한다.';
}

$pausedAt = new \DateTimeImmutable('2026-01-03T00:00:00+00:00');
$thread->close($closedAt);
$thread->pause($pausedAt);

if ($thread->status() !== 'paused') {
    $failures[] = 'pause() 이후 status()는 paused여야 한다.';
}
if ($thread->pausedAt() !== $pausedAt) {
    $failures[] = 'pause() 이후 pausedAt()은 전달한 시각을 반환해야 한다.';
}
if ($thread->closedAt() !== $closedAt) {
    $failures[] = 'pause()는 closedAt()을 리셋하지 않아야 한다(서로 배타적이지 않음).';
}
if ($thread->isPaused() !== true) {
    $failures[] = 'pause() 이후 isPaused()는 true여야 한다.';
}

try {
    new Thread('', 'doc1', '제목', 'user1', $createdAt);
    $failures[] = '빈 id는 EmptyThreadIdError를 던져야 한다.';
} catch (EmptyThreadIdError $e) {
    // 예상된 동작.
}

try {
    new Thread('thread2', '   ', '제목', 'user1', $createdAt);
    $failures[] = '공백만 있는 documentId는 EmptyThreadDocumentIdError를 던져야 한다.';
} catch (EmptyThreadDocumentIdError $e) {
    // 예상된 동작.
}

try {
    new Thread('thread3', 'doc1', '   ', 'user1', $createdAt);
    $failures[] = '공백만 있는 title은 EmptyThreadTitleError를 던져야 한다.';
} catch (EmptyThreadTitleError $e) {
    // 예상된 동작.
}

try {
    new Thread('thread4', 'doc1', '제목', '', $createdAt);
    $failures[] = '빈 createdBy는 EmptyThreadCreatedByError를 던져야 한다.';
} catch (EmptyThreadCreatedByError $e) {
    // 예상된 동작.
}

if ($failures !== []) {
    fwrite(STDERR, "Thread 도메인 모델 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Thread 도메인 모델 테스트 통과.\n");
exit(0);
