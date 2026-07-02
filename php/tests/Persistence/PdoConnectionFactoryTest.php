<?php

declare(strict_types=1);

/**
 * MintWiki\Persistence\PdoConnectionFactory의 DSN 조립 동작을 확인하는
 * smoke test. phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 실제 DB에 연결하는 `connect()`는 여기서 검증하지 않는다 — 네트워크
 * 의존 없이 도는 smoke test 원칙(`php/tests/AutoloadSmokeTest.php`와
 * 동일)을 지키기 위해, DSN 문자열 조립(`dsn()`)만 확인한다. 실제 연결
 * 확인은 `scripts/mariadb_smoke_check.py` / `scripts/postgresql_smoke_check.py`
 * 같은 선택 실행 스크립트가 별도로 담당한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Persistence\ConnectionConfig;
use MintWiki\Persistence\PdoConnectionFactory;

$failures = [];

$postgres = new ConnectionConfig('pgsql', 'localhost', 5432, 'wiki_engine', 'wiki', 'wiki');
$expectedPostgresDsn = 'pgsql:host=localhost;port=5432;dbname=wiki_engine';
if (PdoConnectionFactory::dsn($postgres) !== $expectedPostgresDsn) {
    $failures[] = "dsn()이 PostgreSQL 설정에서 예상한 DSN을 반환하지 않았다: {$expectedPostgresDsn}";
}

$mariadb = new ConnectionConfig('mysql', 'localhost', 3306, 'wiki_engine', 'wiki', 'wiki');
$expectedMariadbDsn = 'mysql:host=localhost;port=3306;dbname=wiki_engine;charset=utf8mb4';
if (PdoConnectionFactory::dsn($mariadb) !== $expectedMariadbDsn) {
    $failures[] = "dsn()이 MariaDB 설정에서 예상한 DSN을 반환하지 않았다: {$expectedMariadbDsn}";
}

$unsupported = new ConnectionConfig('sqlite', ':memory:', 0, '', '', '');
try {
    PdoConnectionFactory::dsn($unsupported);
    $failures[] = 'dsn()이 지원하지 않는 driver에 대해 예외를 던지지 않았다.';
} catch (InvalidArgumentException $exception) {
    // 예상된 경로: 지원하지 않는 driver는 InvalidArgumentException으로 거부되어야 한다.
}

if ($failures !== []) {
    fwrite(STDERR, "PdoConnectionFactory 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "PdoConnectionFactory 테스트 통과.\n");
exit(0);
