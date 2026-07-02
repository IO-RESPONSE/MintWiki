<?php

declare(strict_types=1);

/**
 * MintWiki\User\User value object의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다 (0404 RevisionTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\User\EmptyUsernameError;
use MintWiki\User\User;

$failures = [];

$withoutDisplayName = new User('user1', 'alice');

if ($withoutDisplayName->id() !== 'user1') {
    $failures[] = 'id()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutDisplayName->username() !== 'alice') {
    $failures[] = 'username()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($withoutDisplayName->displayName() !== null) {
    $failures[] = 'displayName 기본값은 null이어야 한다.';
}

$withDisplayName = new User('user2', 'bob', 'Bob Smith');

if ($withDisplayName->displayName() !== 'Bob Smith') {
    $failures[] = 'displayName()이 생성자에 전달한 값을 반환하지 않았다.';
}

$unicodeUser = new User('user3', '한글사용자');

if ($unicodeUser->username() !== '한글사용자') {
    $failures[] = 'username()은 유니코드 값을 그대로 보존해야 한다.';
}

try {
    new User('user4', '');
    $failures[] = '빈 username은 EmptyUsernameError를 던져야 한다.';
} catch (EmptyUsernameError $e) {
    // 예상된 동작.
}

try {
    new User('user5', '   ');
    $failures[] = '공백만 있는 username은 EmptyUsernameError를 던져야 한다.';
} catch (EmptyUsernameError $e) {
    // 예상된 동작.
}

if ($failures !== []) {
    fwrite(STDERR, "User value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "User value object 테스트 통과.\n");
exit(0);
