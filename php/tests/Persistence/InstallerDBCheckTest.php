<?php

declare(strict_types=1);

/**
 * MintWiki\Installer\DBCheck의 데이터베이스 검사 기능을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 실제 in-memory SQLite를 사용하여 데이터베이스 검사 로직을 검증한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Installer\DBCheck;

$failures = [];

// DBCheck 초기화 테스트
try {
    $checker = new DBCheck();
    if ($checker === null) {
        $failures[] = 'DBCheck 초기화가 실패했다.';
    }
} catch (Exception $e) {
    $failures[] = "DBCheck 초기화 실패: " . $e->getMessage();
}

$checker = new DBCheck();

// 연결 유효성 테스트 - 정상
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    if (!$checker->isConnectionValid($connection)) {
        $failures[] = '정상 연결에서 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "정상 연결 테스트 실패: " . $e->getMessage();
}

// 스키마 버전 검사 - 테이블이 없을 때는 예외
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $checker->isSchemaVersionValid($connection);
    $failures[] = '스키마 버전 테이블이 없을 때 RuntimeException을 던져야 한다.';
} catch (RuntimeException $e) {
    // 예상된 동작
    if (strpos($e->getMessage(), '스키마 버전 확인 실패') === false) {
        $failures[] = 'RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// 스키마 버전 검사 - 정상 (1개 이상)
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $connection->exec('
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    ');
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.1.0', '2026-07-02T00:00:00Z')");

    if (!$checker->isSchemaVersionValid($connection)) {
        $failures[] = '스키마 버전이 1개 있을 때 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "스키마 버전 정상 테스트 실패: " . $e->getMessage();
}

// 스키마 버전 검사 - 정상 (여러 개)
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $connection->exec('
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    ');
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.1.0', '2026-07-02T00:00:00Z')");
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.2.0', '2026-07-02T01:00:00Z')");
    $connection->exec("INSERT INTO schema_version (version, applied_at) VALUES ('v0.3.0', '2026-07-02T02:00:00Z')");

    if (!$checker->isSchemaVersionValid($connection)) {
        $failures[] = '스키마 버전이 여러 개 있을 때 true를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "스키마 버전 여러 개 테스트 실패: " . $e->getMessage();
}

// 스키마 버전 검사 - 실패 (빈 테이블)
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $connection->exec('
        CREATE TABLE schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    ');

    if ($checker->isSchemaVersionValid($connection)) {
        $failures[] = '스키마 버전이 0개일 때 false를 반환해야 한다.';
    }
} catch (Exception $e) {
    $failures[] = "스키마 버전 0개 테스트 실패: " . $e->getMessage();
}

// MySQL 방언 테스트 - charset 체크
// SQLite는 charset 설정이 다르므로, 쿼리 구조만 확인하는 통합 테스트
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    // SQLite에서 MySQL 쿼리를 실행하면 예외가 발생해야 함
    // (@@character_set_client는 MySQL 전용)
    // 따라서 RuntimeException으로 wrapping되어야 함
    try {
        $checker->isCharsetValid($connection, 'mysql');
        $failures[] = 'MySQL charset 검사가 지원하지 않는 SQLite 쿼리에서 예외를 던져야 한다.';
    } catch (RuntimeException $e) {
        // 예상된 동작
        if (strpos($e->getMessage(), '문자셋 확인 실패') === false) {
            $failures[] = 'MySQL charset 검사 RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
        }
    }
} catch (Exception $e) {
    $failures[] = "MySQL charset 테스트 실패: " . $e->getMessage();
}

// PostgreSQL 방언 테스트 - encoding 체크
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    // SQLite에서 PostgreSQL 쿼리를 실행하면 예외가 발생해야 함
    try {
        $checker->isCharsetValid($connection, 'pgsql');
        $failures[] = 'PostgreSQL encoding 검사가 지원하지 않는 SQLite 쿼리에서 예외를 던져야 한다.';
    } catch (RuntimeException $e) {
        // 예상된 동작
        if (strpos($e->getMessage(), '문자셋 확인 실패') === false) {
            $failures[] = 'PostgreSQL encoding 검사 RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
        }
    }
} catch (Exception $e) {
    $failures[] = "PostgreSQL encoding 테스트 실패: " . $e->getMessage();
}

// 문자셋 검사 - 지원하지 않는 드라이버
try {
    $connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $checker->isCharsetValid($connection, 'sqlite');
    $failures[] = '지원하지 않는 드라이버에 대해 RuntimeException을 던져야 한다.';
} catch (RuntimeException $e) {
    // 예상된 동작
    if (strpos($e->getMessage(), '지원하지 않는 드라이버') === false) {
        $failures[] = 'RuntimeException 메시지가 올바르지 않다: ' . $e->getMessage();
    }
} catch (Exception $e) {
    $failures[] = "예상하지 않은 예외: " . get_class($e) . " - " . $e->getMessage();
}

// 문자열이 쿼리 구조를 올바르게 처리하는지 확인하는 메서드 테스트
// (실제 charset 검사는 실제 MySQL/PostgreSQL 연결에서 별도로 테스트)
// 여기서는 쿼리 실행이 올바르게 래핑되는지만 확인

// 테스트 결과 출력
if ($failures !== []) {
    fwrite(STDERR, "Installer DBCheck 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "Installer DBCheck 테스트 통과.\n");
exit(0);
