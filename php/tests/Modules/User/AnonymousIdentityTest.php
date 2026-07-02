<?php

declare(strict_types=1);

/**
 * MintWiki\User\AnonymousIdentity value object의 기본 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\User\AnonymousIdentity;

$failures = [];

$identity = new AnonymousIdentity();

if ($identity->isAnonymous() !== true) {
    $failures[] = 'isAnonymous()는 true를 반환해야 한다.';
}

$first = new AnonymousIdentity();
$second = new AnonymousIdentity();

if ($first === $second) {
    $failures[] = 'AnonymousIdentity 인스턴스는 서로 다른 객체여야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AnonymousIdentity value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AnonymousIdentity value object 테스트 통과.\n");
exit(0);
