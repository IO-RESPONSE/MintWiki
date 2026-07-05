<?php

declare(strict_types=1);

/**
 * `MintWiki\Document\RecentDocumentsQuery`의 동작을 확인하는 smoke test
 * (태스크 0693). phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 실제 DB 없이 sqlite in-memory에 `db/schema/document.sql`을 그대로 적용해
 * (1) updated_at 내림차순으로 정렬되는지, (2) limit이 적용되는지,
 * (3) 문서가 없으면 빈 배열을 반환하는지 확인한다 (0693 AccountRepositoryTest.php와
 * 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Document\RecentDocumentsQuery;

$failures = [];

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$documentSql = file_get_contents(__DIR__ . '/../../../../db/schema/document.sql');
if ($documentSql === false) {
    fwrite(STDERR, "db/schema/document.sql을 읽을 수 없습니다.\n");
    exit(1);
}
$connection->exec($documentSql);

/**
 * 지정된 updated_at으로 document row를 직접 삽입한다 (테스트 전용 helper).
 */
function insertDocument(PDO $connection, string $id, string $title, string $updatedAt): void
{
    $statement = $connection->prepare(
        'INSERT INTO document (id, title, normalized_title, current_revision_id, created_at, updated_at) '
        . 'VALUES (:id, :title, :normalized_title, NULL, :created_at, :updated_at)'
    );
    $statement->execute([
        'id' => $id,
        'title' => $title,
        'normalized_title' => $title,
        'created_at' => $updatedAt,
        'updated_at' => $updatedAt,
    ]);
}

// ============================================================================
// (1) 문서가 없으면 빈 배열을 반환해야 한다.
// ============================================================================

$query = new RecentDocumentsQuery($connection);
if ($query->listRecentlyUpdated() !== []) {
    $failures[] = '문서가 없으면 빈 배열을 반환해야 한다.';
}

// ============================================================================
// (2) updated_at 내림차순(최근 순)으로 정렬되어야 한다.
// ============================================================================

insertDocument($connection, 'doc-old', '오래된 문서', '2026-01-01 00:00:00');
insertDocument($connection, 'doc-new', '최신 문서', '2026-06-01 00:00:00');
insertDocument($connection, 'doc-mid', '중간 문서', '2026-03-01 00:00:00');

$results = $query->listRecentlyUpdated();
$titles = array_map(static fn ($document) => $document->title(), $results);

if ($titles !== ['최신 문서', '중간 문서', '오래된 문서']) {
    $failures[] = 'listRecentlyUpdated()는 updated_at 내림차순으로 정렬해야 한다. 실제: ' . implode(', ', $titles);
}

// ============================================================================
// (3) limit이 적용되어야 한다.
// ============================================================================

$limited = $query->listRecentlyUpdated(2);
if (count($limited) !== 2) {
    $failures[] = 'listRecentlyUpdated($limit)는 limit 개수만큼만 반환해야 한다.';
}
if ($limited[0]->title() !== '최신 문서' || $limited[1]->title() !== '중간 문서') {
    $failures[] = 'limit이 적용되어도 정렬 순서는 유지되어야 한다.';
}

if ($failures !== []) {
    fwrite(STDERR, "RecentDocumentsQuery 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "RecentDocumentsQuery 테스트 통과.\n");
exit(0);
