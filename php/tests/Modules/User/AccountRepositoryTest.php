<?php

declare(strict_types=1);

/**
 * MintWiki\User\AccountRepository의 동작을 확인하는 smoke test (태스크 0681).
 * phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 실제 DB 없이 sqlite in-memory에 `db/schema/account.sql`을 그대로 적용해
 * (1) 계정 생성 시 발급된 id/username/해시된 password_hash가 그대로 저장되고,
 * (2) 평문 비밀번호는 저장되지 않으며,
 * (3) username 중복 여부(usernameExists)가 올바르게 판정되고,
 * (4) username UNIQUE 제약을 우회해 중복 생성을 시도하면 예외가 발생하는지 확인한다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\User\AccountRepository;

$failures = [];

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$accountSql = file_get_contents(__DIR__ . '/../../../../db/schema/account.sql');
if ($accountSql === false) {
    fwrite(STDERR, "db/schema/account.sql을 읽을 수 없습니다.\n");
    exit(1);
}
$connection->exec($accountSql);

$repository = new AccountRepository($connection);

// (1) 계정이 존재하지 않으면 usernameExists()는 false를 반환해야 한다.
if ($repository->usernameExists('admin') !== false) {
    $failures[] = '생성 전에는 usernameExists("admin")가 false여야 한다.';
}

// (2) create()는 발급한 id를 반환하고, 실제 행을 저장해야 한다.
$passwordHash = password_hash('correct horse battery staple', PASSWORD_DEFAULT);
$id = $repository->create('admin', $passwordHash);

if (!is_string($id) || $id === '') {
    $failures[] = 'create()는 비어있지 않은 id 문자열을 반환해야 한다.';
}

$row = $connection->query('SELECT id, username, display_name, password_hash FROM account WHERE username = ' . $connection->quote('admin'))
    ->fetch(PDO::FETCH_ASSOC);

if ($row === false) {
    $failures[] = 'create() 이후 account 테이블에 행이 존재해야 한다.';
} else {
    if ($row['id'] !== $id) {
        $failures[] = '저장된 id가 create()가 반환한 id와 일치해야 한다.';
    }
    if ($row['password_hash'] !== $passwordHash) {
        $failures[] = '저장된 password_hash가 전달한 해시와 정확히 일치해야 한다.';
    }
    if (str_contains((string) $row['password_hash'], 'correct horse battery staple')) {
        $failures[] = 'password_hash 컬럼에 평문 비밀번호가 그대로 남아있으면 안 된다.';
    }
    if (!password_verify('correct horse battery staple', (string) $row['password_hash'])) {
        $failures[] = '저장된 password_hash는 원래 평문 비밀번호로 검증되어야 한다.';
    }
}

// (3) 생성 후에는 usernameExists()가 true를 반환해야 한다.
if ($repository->usernameExists('admin') !== true) {
    $failures[] = '생성 후에는 usernameExists("admin")가 true여야 한다.';
}

// (4) UNIQUE 제약 위반 시 예외가 발생해야 한다(중복 생성 방지).
try {
    $repository->create('admin', password_hash('another-password', PASSWORD_DEFAULT));
    $failures[] = '중복된 username으로 create()를 호출하면 예외가 발생해야 한다.';
} catch (PDOException $exception) {
    // 기대된 동작.
}

// (5) findByUsername()은 존재하는 계정 행을 그대로 반환해야 한다(태스크 0686, 로그인 대조용).
$foundByUsername = $repository->findByUsername('admin');
if ($foundByUsername === null) {
    $failures[] = 'findByUsername("admin")은 생성된 계정을 반환해야 한다.';
} elseif ($foundByUsername['id'] !== $id || $foundByUsername['password_hash'] !== $passwordHash) {
    $failures[] = 'findByUsername("admin")이 반환한 행은 create()가 저장한 id/password_hash와 일치해야 한다.';
}

// (6) findByUsername()은 존재하지 않는 username에 대해 null을 반환해야 한다.
if ($repository->findByUsername('no-such-user') !== null) {
    $failures[] = '존재하지 않는 username의 findByUsername()은 null을 반환해야 한다.';
}

// (7) findById()는 존재하는 계정 행을 그대로 반환해야 한다(태스크 0686, 세션 복원용).
$foundById = $repository->findById($id);
if ($foundById === null) {
    $failures[] = 'findById()는 생성된 계정을 반환해야 한다.';
} elseif ($foundById['username'] !== 'admin') {
    $failures[] = 'findById()가 반환한 행의 username은 "admin"이어야 한다.';
}

// (8) findById()는 존재하지 않는 id에 대해 null을 반환해야 한다.
if ($repository->findById('no-such-id') !== null) {
    $failures[] = '존재하지 않는 id의 findById()는 null을 반환해야 한다.';
}

// (9) block()은 blocked_at을 채워야 한다(태스크 0699, 사용자 차단).
$blockedAtBefore = $connection->query('SELECT blocked_at FROM account WHERE id = ' . $connection->quote($id))->fetchColumn();
if ($blockedAtBefore !== null) {
    $failures[] = 'block() 호출 전 blocked_at은 NULL이어야 한다.';
}

$repository->block($id);

$blockedAtAfter = $connection->query('SELECT blocked_at FROM account WHERE id = ' . $connection->quote($id))->fetchColumn();
if ($blockedAtAfter === null || $blockedAtAfter === false || (string) $blockedAtAfter === '') {
    $failures[] = 'block() 호출 후 blocked_at이 채워져 있어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "AccountRepository 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "AccountRepository 테스트 통과.\n");
exit(0);
