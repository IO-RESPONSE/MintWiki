<?php

declare(strict_types=1);

/**
 * `MintWiki\Security\SessionUserResolver`(태스크 0686)의 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다. 실제 DB 없이 sqlite
 * in-memory에 `db/schema/account.sql`을 적용해 세션 → 사용자 복원 흐름을
 * 검증한다.
 *
 * 검증 대상:
 * (1) 세션에 로그인 식별자가 없으면 resolve()는 null을 반환한다(익명).
 * (2) 세션에 존재하는 계정 id가 있으면 resolve()는 해당 계정의 `User`를
 *     반환하고, id/username이 일치한다.
 * (3) 세션에 저장된 계정 id가 가리키는 계정이 더 이상 존재하지 않으면(삭제됨)
 *     resolve()는 null을 반환한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Security\PhpSessionAdapter;
use MintWiki\Security\SessionUserResolver;
use MintWiki\User\AccountRepository;

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$failures = [];
$accountSql = file_get_contents(__DIR__ . '/../../../db/schema/account.sql');
if ($accountSql === false) {
    fwrite(STDERR, "db/schema/account.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connection->exec($accountSql);

$accountRepository = new AccountRepository($connection);
$accountId = $accountRepository->create('admin', password_hash('correct horse battery staple', PASSWORD_DEFAULT));

// (1) 세션에 로그인 식별자가 없으면 null을 반환해야 한다.
$_SESSION = [];
$resolver = new SessionUserResolver(new PhpSessionAdapter(), $accountRepository);

if ($resolver->resolve() !== null) {
    $failures[] = '세션에 로그인 식별자가 없으면 resolve()는 null을 반환해야 한다.';
}

// (2) 세션에 존재하는 계정 id가 있으면 해당 계정의 User를 반환해야 한다.
$_SESSION = [SessionUserResolver::SESSION_KEY => $accountId];

$resolvedUser = $resolver->resolve();
if ($resolvedUser === null) {
    $failures[] = '세션에 유효한 계정 id가 있으면 resolve()는 User를 반환해야 한다.';
} else {
    if ($resolvedUser->id() !== $accountId) {
        $failures[] = '복원된 User의 id는 세션에 저장된 계정 id와 일치해야 한다.';
    }
    if ($resolvedUser->username() !== 'admin') {
        $failures[] = '복원된 User의 username은 "admin"이어야 한다.';
    }
}

// (3) 세션에 저장된 계정 id의 계정이 존재하지 않으면(삭제됨) null을 반환해야 한다.
$_SESSION = [SessionUserResolver::SESSION_KEY => 'no-such-account-id'];

if ($resolver->resolve() !== null) {
    $failures[] = '세션의 계정 id가 가리키는 계정이 없으면 resolve()는 null을 반환해야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "SessionUserResolver 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "SessionUserResolver 테스트 통과.\n");
exit(0);
