<?php

declare(strict_types=1);

/**
 * MintWiki\Document\Document value object의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0395 ResponseTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\Document;

$failures = [];

$withoutRevision = new Document('doc-1', 'Title');

if ($withoutRevision->id() !== 'doc-1') {
    $failures[] = 'id()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutRevision->title() !== 'Title') {
    $failures[] = 'title()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutRevision->normalizedTitle() !== 'Title') {
    $failures[] = 'normalizedTitle()이 title()과 같은 값을 반환하지 않았다.';
}
if ($withoutRevision->currentRevisionId() !== null) {
    $failures[] = 'currentRevisionId 기본값은 null이어야 한다.';
}

$withRevision = new Document('doc-2', 'Another Title', 'rev-1');

if ($withRevision->currentRevisionId() !== 'rev-1') {
    $failures[] = 'currentRevisionId()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withRevision->id() !== 'doc-2') {
    $failures[] = 'id()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withRevision->title() !== 'Another Title') {
    $failures[] = 'title()이 생성자에 전달한 값을 반환하지 않았다.';
}

if ($failures !== []) {
    fwrite(STDERR, "Document value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Document value object 테스트 통과.\n");
exit(0);
