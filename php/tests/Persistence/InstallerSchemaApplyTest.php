<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\SchemaApply(태스크 0680에서 실제 SQL 적용을 연결)의 동작을
 * 확인하는 smoke test. phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 검증 대상:
 * (1) 기본 schemaDir()이 실제 `db/schema` 디렉터리를 가리킨다.
 * (2) 기본 schemaDir()의 SQL을 FK 의존 순서로 전부 적용하면 12개 테이블이 모두
 *     생성되고 `schema_version`에 버전 행이 기록된다.
 * (3) 존재하지 않는 스키마 파일이 있으면 RuntimeException을 던지고 파일 이름을
 *     메시지에 포함한다.
 * (4) SQL 실행이 실패하는 파일이 있으면 RuntimeException을 던지고 파일 이름을
 *     메시지에 포함하며, 실패 이전 파일들은 이미 적용된 채로 남는다(DDL은
 *     트랜잭션으로 되돌리지 않는다).
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\SchemaApply;

const SCHEMA_APPLY_TEST_ORDER = [
    'schema_migration.sql',
    'schema_version.sql',
    'account.sql',
    'document.sql',
    'revision.sql',
    'user_session.sql',
    'acl_rule.sql',
    'acl_namespace_rule.sql',
    'discussion_thread.sql',
    'discussion_comment.sql',
    'audit_event.sql',
    'job.sql',
];

$failures = [];
$realSchemaDir = dirname(__DIR__, 3) . '/db/schema';

// (1) 기본 schemaDir()은 실제 db/schema 디렉터리를 가리켜야 한다.
$schemaApply = new SchemaApply();
if ($schemaApply->schemaDir() !== $realSchemaDir) {
    $failures[] = "기본 schemaDir()이 실제 db/schema를 가리켜야 하는데 '{$schemaApply->schemaDir()}'이었다.";
}
if (!is_dir($schemaApply->schemaDir())) {
    $failures[] = '기본 schemaDir()이 존재하는 디렉터리를 가리켜야 한다.';
}

// (2) 기본 schemaDir()의 SQL을 전부 적용하면 12개 테이블이 생성되고 schema_version이 채워져야 한다.
try {
    $pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec('PRAGMA foreign_keys = ON');

    $applied = $schemaApply->apply($pdo, 'v0.1.0');

    if ($applied !== SCHEMA_APPLY_TEST_ORDER) {
        $failures[] = 'apply()는 SCHEMA_ORDER 순서대로 적용한 파일 이름 목록을 반환해야 한다.';
    }

    $tables = $pdo->query("SELECT name FROM sqlite_master WHERE type = 'table'")->fetchAll(PDO::FETCH_COLUMN);
    $expectedTables = array_map(static fn (string $filename): string => substr($filename, 0, -4), SCHEMA_APPLY_TEST_ORDER);
    $missingTables = array_diff($expectedTables, $tables);
    if ($missingTables !== []) {
        $failures[] = '스키마 적용 후 생성되지 않은 테이블: ' . implode(', ', $missingTables);
    }

    $versionRow = $pdo->query('SELECT version FROM schema_version')->fetch(PDO::FETCH_ASSOC);
    if (($versionRow['version'] ?? null) !== 'v0.1.0') {
        $failures[] = 'schema_version에 적용한 버전 문자열이 기록되어 있어야 한다.';
    }
} catch (Exception $e) {
    $failures[] = '기본 schemaDir() 전체 적용이 예외를 던지면 안 된다: ' . $e->getMessage();
}

// (3) 존재하지 않는 스키마 파일이 있으면 RuntimeException을 던져야 한다.
$missingFileDir = sys_get_temp_dir() . '/mintwiki_schema_apply_missing_' . getmypid();
if (!mkdir($missingFileDir, 0777, true) && !is_dir($missingFileDir)) {
    fwrite(STDERR, "테스트 디렉터리를 만들 수 없습니다: {$missingFileDir}\n");
    exit(1);
}

try {
    copy($realSchemaDir . '/schema_migration.sql', $missingFileDir . '/schema_migration.sql');
    // schema_version.sql은 일부러 두지 않는다 — SCHEMA_ORDER의 두 번째 파일이 없어야 한다.

    $missingFileSchemaApply = new SchemaApply($missingFileDir);
    $pdoForMissing = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    try {
        $missingFileSchemaApply->apply($pdoForMissing, 'v0.1.0');
        $failures[] = '스키마 파일이 없으면 RuntimeException을 던져야 한다.';
    } catch (RuntimeException $e) {
        if (strpos($e->getMessage(), 'schema_version.sql') === false) {
            $failures[] = "누락 파일 예외 메시지에 파일 이름이 포함되어야 하는데 '{$e->getMessage()}'이었다.";
        }
    }
} finally {
    @unlink($missingFileDir . '/schema_migration.sql');
    @rmdir($missingFileDir);
}

// (4) SQL 실행이 실패하는 파일이 있으면 RuntimeException을 던지고, 그 이전 파일은 이미 적용되어야 한다.
$badSqlDir = sys_get_temp_dir() . '/mintwiki_schema_apply_bad_sql_' . getmypid();
if (!mkdir($badSqlDir, 0777, true) && !is_dir($badSqlDir)) {
    fwrite(STDERR, "테스트 디렉터리를 만들 수 없습니다: {$badSqlDir}\n");
    exit(1);
}

try {
    copy($realSchemaDir . '/schema_migration.sql', $badSqlDir . '/schema_migration.sql');
    copy($realSchemaDir . '/schema_version.sql', $badSqlDir . '/schema_version.sql');
    file_put_contents($badSqlDir . '/account.sql', 'THIS IS NOT VALID SQL;');

    $badSqlSchemaApply = new SchemaApply($badSqlDir);
    $pdoForBadSql = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    try {
        $badSqlSchemaApply->apply($pdoForBadSql, 'v0.1.0');
        $failures[] = '실패하는 SQL이 있으면 RuntimeException을 던져야 한다.';
    } catch (RuntimeException $e) {
        if (strpos($e->getMessage(), 'account.sql') === false) {
            $failures[] = "SQL 실행 실패 예외 메시지에 파일 이름이 포함되어야 하는데 '{$e->getMessage()}'이었다.";
        }
    }

    $tablesAfterFailure = $pdoForBadSql->query("SELECT name FROM sqlite_master WHERE type = 'table'")->fetchAll(PDO::FETCH_COLUMN);
    if (!in_array('schema_migration', $tablesAfterFailure, true) || !in_array('schema_version', $tablesAfterFailure, true)) {
        $failures[] = '실패 이전에 적용된 테이블(schema_migration, schema_version)은 그대로 남아 있어야 한다.';
    }

    $versionCountAfterFailure = (int) $pdoForBadSql->query('SELECT COUNT(*) FROM schema_version')->fetchColumn();
    if ($versionCountAfterFailure !== 0) {
        $failures[] = '적용이 실패하면 schema_version에 행이 기록되면 안 된다.';
    }
} finally {
    @unlink($badSqlDir . '/schema_migration.sql');
    @unlink($badSqlDir . '/schema_version.sql');
    @unlink($badSqlDir . '/account.sql');
    @rmdir($badSqlDir);
}

if ($failures !== []) {
    fwrite(STDERR, "Installer SchemaApply 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Installer SchemaApply 테스트 통과.\n");
exit(0);
