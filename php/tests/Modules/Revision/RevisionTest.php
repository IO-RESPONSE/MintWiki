<?php

declare(strict_types=1);

/**
 * MintWiki\Revision\Revision value object의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0400 DocumentTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Revision\Revision;

$failures = [];

$withoutParent = new Revision('rev1', 'doc1', 'Hello, World!', 'user1', 'Initial content');

if ($withoutParent->id() !== 'rev1') {
    $failures[] = 'id()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutParent->documentId() !== 'doc1') {
    $failures[] = 'documentId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutParent->source() !== 'Hello, World!') {
    $failures[] = 'source()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutParent->authorId() !== 'user1') {
    $failures[] = 'authorId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutParent->summary() !== 'Initial content') {
    $failures[] = 'summary()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutParent->parentRevisionId() !== null) {
    $failures[] = 'parentRevisionId 기본값은 null이어야 한다.';
}
if ($withoutParent->createdAt() !== null) {
    $failures[] = 'createdAt 기본값은 null이어야 한다.';
}

$withCreatedAt = new Revision('rev-ts', 'doc1', 'content', 'user1', 'summary', null, '2026-07-01 00:00:00');
if ($withCreatedAt->createdAt() !== '2026-07-01 00:00:00') {
    $failures[] = 'createdAt()이 생성자에 전달한 값을 반환하지 않았다.';
}

$withParent = new Revision('rev2', 'doc1', 'Updated content', 'user2', 'Update content', 'rev1');

if ($withParent->parentRevisionId() !== 'rev1') {
    $failures[] = 'parentRevisionId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withParent->id() !== 'rev2') {
    $failures[] = 'id()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withParent->documentId() !== 'doc1') {
    $failures[] = 'documentId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withParent->source() !== 'Updated content') {
    $failures[] = 'source()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withParent->authorId() !== 'user2') {
    $failures[] = 'authorId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withParent->summary() !== 'Update content') {
    $failures[] = 'summary()가 생성자에 전달한 값을 반환하지 않았다.';
}

$multiline = new Revision('rev3', 'doc2', "Multi-line\ncontent\nhere", 'user3', 'Complex edit', 'rev2');

if ($multiline->source() !== "Multi-line\ncontent\nhere") {
    $failures[] = 'source()는 정규화 없이 원본 값을 그대로 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Revision value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Revision value object 테스트 통과.\n");
exit(0);
