<?php

declare(strict_types=1);

/**
 * MintWiki\Persistence\PdoTransaction의 begin/commit/rollback 위임 동작을
 * 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 실제 PostgreSQL/MariaDB 연결 없이도 트랜잭션 경계 자체(커밋된 행이
 * 남는지, 롤백된 행이 사라지는지)를 검증하기 위해, 네트워크가 필요 없는
 * `pdo_sqlite`(in-memory) 연결을 사용한다. 이 클래스는 드라이버에 상관없이
 * 순수하게 `PDO`의 트랜잭션 메서드를 위임하므로, sqlite 위에서의 검증은
 * pgsql/mysql 드라이버에도 그대로 성립한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Persistence\PdoTransaction;

$failures = [];

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connection->exec('CREATE TABLE widgets (name TEXT NOT NULL)');

$transaction = new PdoTransaction($connection);

// commit()은 그 안에서 실행한 변경을 남겨야 한다.
$transaction->begin();
$connection->exec("INSERT INTO widgets (name) VALUES ('kept')");
$transaction->commit();

$afterCommit = (int) $connection->query('SELECT COUNT(*) FROM widgets')->fetchColumn();
if ($afterCommit !== 1) {
    $failures[] = "commit() 이후 행이 남아 있어야 하는데 개수가 {$afterCommit}이다.";
}

// rollback()은 그 안에서 실행한 변경을 취소해야 한다.
$transaction->begin();
$connection->exec("INSERT INTO widgets (name) VALUES ('discarded')");
$transaction->rollback();

$afterRollback = (int) $connection->query('SELECT COUNT(*) FROM widgets')->fetchColumn();
if ($afterRollback !== 1) {
    $failures[] = "rollback() 이후 행 개수가 commit() 시점(1)과 같아야 하는데 {$afterRollback}이다.";
}

if ($failures !== []) {
    fwrite(STDERR, "PdoTransaction 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "PdoTransaction 테스트 통과.\n");
exit(0);
