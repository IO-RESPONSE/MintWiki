<?php

declare(strict_types=1);

/**
 * MintWiki\Discussion\Comment 도메인 모델의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0409 UserTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\Comment;
use MintWiki\Discussion\EmptyCommentBodyError;
use MintWiki\Discussion\EmptyCommentCreatedByError;
use MintWiki\Discussion\EmptyCommentIdError;
use MintWiki\Discussion\EmptyCommentThreadIdError;

$failures = [];

$createdAt = new \DateTimeImmutable('2026-01-01T00:00:00+00:00');
$comment = new Comment('comment1', 'thread1', '  본문  그대로  ', 'user1', $createdAt);

if ($comment->id() !== 'comment1') {
    $failures[] = 'id()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($comment->threadId() !== 'thread1') {
    $failures[] = 'threadId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($comment->body() !== '  본문  그대로  ') {
    $failures[] = 'body()는 정규화 없이 생성자에 전달한 값을 그대로 반환해야 한다.';
}
if ($comment->createdBy() !== 'user1') {
    $failures[] = 'createdBy()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($comment->createdAt() !== $createdAt) {
    $failures[] = 'createdAt()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($comment->isHidden() !== false) {
    $failures[] = 'isHidden() 기본값은 false여야 한다.';
}
if ($comment->hiddenAt() !== null) {
    $failures[] = 'hiddenAt() 기본값은 null이어야 한다.';
}

$publicView = $comment->toPublicView();
if ($publicView['body'] !== $comment->body()) {
    $failures[] = '숨겨지지 않은 댓글의 toPublicView()는 실제 body를 노출해야 한다.';
}

$moderatorView = $comment->toModeratorView();
if ($moderatorView['body'] !== $comment->body()) {
    $failures[] = 'toModeratorView()는 항상 실제 body를 노출해야 한다.';
}

$hiddenAt = new \DateTimeImmutable('2026-01-02T00:00:00+00:00');
$comment->hide($hiddenAt);

if ($comment->isHidden() !== true) {
    $failures[] = 'hide() 이후 isHidden()은 true여야 한다.';
}
if ($comment->hiddenAt() !== $hiddenAt) {
    $failures[] = 'hide() 이후 hiddenAt()은 전달한 시각을 반환해야 한다.';
}
if ($comment->body() !== '  본문  그대로  ') {
    $failures[] = 'hide()는 body를 지우거나 덮어쓰지 않아야 한다.';
}

$publicViewAfterHide = $comment->toPublicView();
if ($publicViewAfterHide['body'] !== null) {
    $failures[] = '숨겨진 댓글의 toPublicView()는 body를 null로 가려야 한다.';
}
if ($publicViewAfterHide['is_hidden'] !== true || $publicViewAfterHide['hidden_at'] !== $hiddenAt) {
    $failures[] = 'toPublicView()는 is_hidden/hidden_at 필드를 그대로 노출해야 한다.';
}

$moderatorViewAfterHide = $comment->toModeratorView();
if ($moderatorViewAfterHide['body'] !== '  본문  그대로  ') {
    $failures[] = '숨겨진 댓글에도 toModeratorView()는 실제 body를 노출해야 한다.';
}

$reHiddenAt = new \DateTimeImmutable('2026-01-03T00:00:00+00:00');
$comment->hide($reHiddenAt);

if ($comment->hiddenAt() !== $reHiddenAt) {
    $failures[] = 'hide()는 이미 숨겨진 댓글에도 멱등하게 재적용되어 hiddenAt을 갱신해야 한다.';
}

try {
    new Comment('', 'thread1', '본문', 'user1', $createdAt);
    $failures[] = '빈 id는 EmptyCommentIdError를 던져야 한다.';
} catch (EmptyCommentIdError $e) {
    // 예상된 동작.
}

try {
    new Comment('comment2', '   ', '본문', 'user1', $createdAt);
    $failures[] = '공백만 있는 threadId는 EmptyCommentThreadIdError를 던져야 한다.';
} catch (EmptyCommentThreadIdError $e) {
    // 예상된 동작.
}

try {
    new Comment('comment3', 'thread1', '   ', 'user1', $createdAt);
    $failures[] = '공백만 있는 body는 EmptyCommentBodyError를 던져야 한다.';
} catch (EmptyCommentBodyError $e) {
    // 예상된 동작.
}

try {
    new Comment('comment4', 'thread1', '본문', '', $createdAt);
    $failures[] = '빈 createdBy는 EmptyCommentCreatedByError를 던져야 한다.';
} catch (EmptyCommentCreatedByError $e) {
    // 예상된 동작.
}

if ($failures !== []) {
    fwrite(STDERR, "Comment 도메인 모델 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Comment 도메인 모델 테스트 통과.\n");
exit(0);
