<?php

declare(strict_types=1);

/**
 * MintWiki\Persistence\SeedLoader의 seed fixture 로딩 기능을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다.
 *
 * ANSI SQL 기반의 INSERT 문을 파싱하여 데이터베이스에 로드하는지 검증한다.
 * 실제 PostgreSQL/MariaDB 연결 없이 in-memory SQLite를 사용한다.
 */

$autoloadFile = __DIR__ . '/../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Persistence\SeedLoader;

$failures = [];

// SeedLoader 초기화 테스트
try {
    $loader = new SeedLoader();
    if ($loader->getFixturesDir() === '' || $loader->getFixturesDir() === null) {
        $failures[] = 'SeedLoader 기본 fixtures 디렉토리가 설정되지 않았다.';
    }
} catch (Exception $e) {
    $failures[] = "SeedLoader 초기화 실패: " . $e->getMessage();
}

// 커스텀 경로로 SeedLoader 초기화
$customFixturesDir = __DIR__ . '/../fixtures/seed';
try {
    $loader = new SeedLoader($customFixturesDir);
    if ($loader->getFixturesDir() !== $customFixturesDir) {
        $failures[] = 'SeedLoader 커스텀 fixtures 디렉토리가 올바르게 설정되지 않았다.';
    }
} catch (Exception $e) {
    $failures[] = "SeedLoader 커스텀 초기화 실패: " . $e->getMessage();
}

// 존재하지 않는 디렉토리로 초기화하면 예외가 발생해야 한다
try {
    $loader = new SeedLoader('/nonexistent/fixtures/seed');
    $failures[] = 'SeedLoader가 존재하지 않는 디렉토리에서 예외를 던져야 한다.';
} catch (RuntimeException $e) {
    // 예상된 동작
}

// Seed 파일 존재 확인
$documentsFile = $customFixturesDir . '/documents.sql';
$revisionsFile = $customFixturesDir . '/revisions.sql';

if (!file_exists($documentsFile)) {
    $failures[] = "documents.sql 파일을 찾을 수 없다: {$documentsFile}";
}
if (!file_exists($revisionsFile)) {
    $failures[] = "revisions.sql 파일을 찾을 수 없다: {$revisionsFile}";
}

// SQL 파싱 테스트
$loader = new SeedLoader($customFixturesDir);

// 간단한 INSERT 문 파싱 테스트 (리플렉션을 사용하여 private 메서드 호출)
$reflectionMethod = new ReflectionMethod(SeedLoader::class, 'parseInsertStatements');
$reflectionMethod->setAccessible(true);

// 단순 INSERT 파싱
$simpleSql = "INSERT INTO test_table (id, name) VALUES ('1', 'Test');";
$statements = $reflectionMethod->invoke($loader, $simpleSql);
if (count($statements) !== 1) {
    $failures[] = "단순 INSERT 문 파싱 실패: " . count($statements) . "개 발견됨";
}

// 여러 INSERT 파싱
$multipleSql = <<<SQL
INSERT INTO table1 (id) VALUES ('1');
INSERT INTO table2 (id) VALUES ('2');
SQL;
$statements = $reflectionMethod->invoke($loader, $multipleSql);
if (count($statements) !== 2) {
    $failures[] = "여러 INSERT 문 파싱 실패: " . count($statements) . "개 발견됨";
}

// 라인 주석 제거 테스트
$commentSql = <<<SQL
-- 이것은 주석입니다
INSERT INTO test_table (id) VALUES ('1'); -- 인라인 주석
SQL;
$statements = $reflectionMethod->invoke($loader, $commentSql);
if (count($statements) !== 1) {
    $failures[] = "라인 주석 제거 파싱 실패: " . count($statements) . "개 발견됨";
}
if (!empty($statements) && strpos($statements[0], '--') !== false) {
    $failures[] = "라인 주석이 완전히 제거되지 않았다.";
}

// 블록 주석 제거 테스트
$blockCommentSql = <<<SQL
/* 이것은 블록 주석입니다 */
INSERT INTO test_table (id) VALUES ('1');
SQL;
$statements = $reflectionMethod->invoke($loader, $blockCommentSql);
if (count($statements) !== 1) {
    $failures[] = "블록 주석 제거 파싱 실패: " . count($statements) . "개 발견됨";
}

// 여러 줄 VALUES 파싱
$multilineSql = <<<SQL
INSERT INTO test_table (id, name)
VALUES (
    'id-1',
    'Test Name'
);
SQL;
$statements = $reflectionMethod->invoke($loader, $multilineSql);
if (count($statements) !== 1) {
    $failures[] = "여러 줄 VALUES 파싱 실패: " . count($statements) . "개 발견됨";
}

// 데이터베이스 로딩 테스트
$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

// 테이블 생성
$connection->exec('
    CREATE TABLE document (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        normalized_title TEXT NOT NULL,
        current_revision_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
');
$connection->exec('
    CREATE TABLE revision (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        source TEXT NOT NULL,
        author_id TEXT NOT NULL,
        summary TEXT NOT NULL,
        parent_revision_id TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (document_id) REFERENCES document(id)
    )
');

// documents seed 로드
try {
    $loader->loadSeed($connection, 'documents');
} catch (Exception $e) {
    $failures[] = "documents seed 로드 실패: " . $e->getMessage();
}

// 로드된 문서 개수 확인
$count = (int) $connection->query('SELECT COUNT(*) FROM document')->fetchColumn();
if ($count !== 3) {
    $failures[] = "documents 로드 후 행 개수가 3이 아니다: {$count}";
}

// 로드된 문서 데이터 확인
$doc = $connection->query(
    "SELECT title FROM document WHERE id = 'doc-00001-0000-0000-0000-000000000000'"
)->fetch(PDO::FETCH_ASSOC);
if (!$doc || $doc['title'] !== 'Home') {
    $failures[] = "documents의 첫 번째 문서의 title이 올바르지 않다.";
}

// revisions seed 로드
try {
    $loader->loadSeed($connection, 'revisions');
} catch (Exception $e) {
    $failures[] = "revisions seed 로드 실패: " . $e->getMessage();
}

// 로드된 리비전 개수 확인
$revCount = (int) $connection->query('SELECT COUNT(*) FROM revision')->fetchColumn();
if ($revCount !== 4) {
    $failures[] = "revisions 로드 후 행 개수가 4가 아니다: {$revCount}";
}

// loadAllSeeds 테스트
$connection2 = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connection2->exec('
    CREATE TABLE document (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        normalized_title TEXT NOT NULL,
        current_revision_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
');
$connection2->exec('
    CREATE TABLE revision (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        source TEXT NOT NULL,
        author_id TEXT NOT NULL,
        summary TEXT NOT NULL,
        parent_revision_id TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (document_id) REFERENCES document(id)
    )
');

try {
    $loader->loadAllSeeds($connection2);
} catch (Exception $e) {
    $failures[] = "loadAllSeeds 실패: " . $e->getMessage();
}

$docCount2 = (int) $connection2->query('SELECT COUNT(*) FROM document')->fetchColumn();
$revCount2 = (int) $connection2->query('SELECT COUNT(*) FROM revision')->fetchColumn();

if ($docCount2 !== 3) {
    $failures[] = "loadAllSeeds 후 document 행 개수가 3이 아니다: {$docCount2}";
}
if ($revCount2 !== 4) {
    $failures[] = "loadAllSeeds 후 revision 행 개수가 4가 아니다: {$revCount2}";
}

// 존재하지 않는 seed 파일 로드 시 예외 발생 확인
$connection3 = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
try {
    $loader->loadSeed($connection3, 'nonexistent_table');
    $failures[] = 'loadSeed()가 존재하지 않는 파일 로드 시 예외를 던져야 한다.';
} catch (RuntimeException $e) {
    // 예상된 동작
}

// 테스트 결과 출력
if ($failures !== []) {
    fwrite(STDERR, "SeedLoader 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "SeedLoader 테스트 통과.\n");
exit(0);
