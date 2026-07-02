<?php

declare(strict_types=1);

/**
 * MintWiki\Persistence\SqlDialect enum의 기본 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Persistence\SqlDialect;

$failures = [];

// MySQL enum 케이스 테스트
$mysql = SqlDialect::MySQL;
if ($mysql->value !== 'mysql') {
    $failures[] = 'MySQL enum의 value가 "mysql"이 아니다.';
}

// PostgreSQL enum 케이스 테스트
$postgresql = SqlDialect::PostgreSQL;
if ($postgresql->value !== 'pgsql') {
    $failures[] = 'PostgreSQL enum의 value가 "pgsql"이 아니다.';
}

// SQLite enum 케이스 테스트
$sqlite = SqlDialect::SQLite;
if ($sqlite->value !== 'sqlite') {
    $failures[] = 'SQLite enum의 value가 "sqlite"이 아니다.';
}

// tryFrom() 메서드 테스트
if (SqlDialect::tryFrom('mysql') !== SqlDialect::MySQL) {
    $failures[] = 'tryFrom("mysql")이 MySQL 케이스를 반환하지 않았다.';
}
if (SqlDialect::tryFrom('pgsql') !== SqlDialect::PostgreSQL) {
    $failures[] = 'tryFrom("pgsql")이 PostgreSQL 케이스를 반환하지 않았다.';
}
if (SqlDialect::tryFrom('sqlite') !== SqlDialect::SQLite) {
    $failures[] = 'tryFrom("sqlite")이 SQLite 케이스를 반환하지 않았다.';
}

// tryFromDriver() 메서드 테스트
if (SqlDialect::tryFromDriver('mysql') !== SqlDialect::MySQL) {
    $failures[] = 'tryFromDriver("mysql")이 MySQL 케이스를 반환하지 않았다.';
}
if (SqlDialect::tryFromDriver('pgsql') !== SqlDialect::PostgreSQL) {
    $failures[] = 'tryFromDriver("pgsql")이 PostgreSQL 케이스를 반환하지 않았다.';
}
if (SqlDialect::tryFromDriver('sqlite') !== SqlDialect::SQLite) {
    $failures[] = 'tryFromDriver("sqlite")이 SQLite 케이스를 반환하지 않았다.';
}

// tryFromDriver() 지원하지 않는 값 테스트
if (SqlDialect::tryFromDriver('unsupported') !== null) {
    $failures[] = 'tryFromDriver("unsupported")이 null을 반환하지 않았다.';
}

// fromDriver() 메서드 테스트
if (SqlDialect::fromDriver('mysql') !== SqlDialect::MySQL) {
    $failures[] = 'fromDriver("mysql")이 MySQL 케이스를 반환하지 않았다.';
}
if (SqlDialect::fromDriver('pgsql') !== SqlDialect::PostgreSQL) {
    $failures[] = 'fromDriver("pgsql")이 PostgreSQL 케이스를 반환하지 않았다.';
}
if (SqlDialect::fromDriver('sqlite') !== SqlDialect::SQLite) {
    $failures[] = 'fromDriver("sqlite")이 SQLite 케이스를 반환하지 않았다.';
}

// fromDriver() 지원하지 않는 값 테스트
try {
    SqlDialect::fromDriver('unsupported');
    $failures[] = 'fromDriver("unsupported")이 예외를 던지지 않았다.';
} catch (InvalidArgumentException $exception) {
    // 예상된 경로: 지원하지 않는 driver는 InvalidArgumentException으로 거부되어야 한다.
}

if ($failures !== []) {
    fwrite(STDERR, "SqlDialect enum 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "SqlDialect enum 테스트 통과.\n");
exit(0);
