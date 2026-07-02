<?php

declare(strict_types=1);

/**
 * MintWiki\Persistence\ConnectionConfig value object의 기본 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다 (0395 ResponseTest.php와
 * 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Persistence\ConnectionConfig;

$failures = [];

$config = new ConnectionConfig('pgsql', 'localhost', 5432, 'wiki_engine', 'wiki', 'wiki');

if ($config->driver() !== 'pgsql') {
    $failures[] = 'driver()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($config->host() !== 'localhost') {
    $failures[] = 'host()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($config->port() !== 5432) {
    $failures[] = 'port()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($config->database() !== 'wiki_engine') {
    $failures[] = 'database()가 생성자에 전달한 값을 반환하지 않았다.';
}
if ($config->username() !== 'wiki') {
    $failures[] = 'username()이 생성자에 전달한 값을 반환하지 않았다.';
}
if ($config->password() !== 'wiki') {
    $failures[] = 'password()가 생성자에 전달한 값을 반환하지 않았다.';
}

if ($failures !== []) {
    fwrite(STDERR, "ConnectionConfig value object 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "ConnectionConfig value object 테스트 통과.\n");
exit(0);
