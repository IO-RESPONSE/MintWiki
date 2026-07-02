<?php

declare(strict_types=1);

/**
 * MintWiki\Discussion\ThreadState enum의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0409 UserTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Discussion\ThreadState;

$failures = [];

if (ThreadState::Open->value !== 'open') {
    $failures[] = 'ThreadState::Open의 값은 open이어야 한다.';
}
if (ThreadState::Closed->value !== 'closed') {
    $failures[] = 'ThreadState::Closed의 값은 closed여야 한다.';
}
if (ThreadState::Paused->value !== 'paused') {
    $failures[] = 'ThreadState::Paused의 값은 paused여야 한다.';
}
if (ThreadState::from('open') !== ThreadState::Open) {
    $failures[] = "ThreadState::from('open')은 ThreadState::Open을 반환해야 한다.";
}

if ($failures !== []) {
    fwrite(STDERR, "ThreadState enum 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "ThreadState enum 테스트 통과.\n");
exit(0);
