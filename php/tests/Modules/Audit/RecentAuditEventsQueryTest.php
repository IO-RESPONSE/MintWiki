<?php

declare(strict_types=1);

/**
 * `MintWiki\Audit\RecentAuditEventsQuery`의 동작을 확인하는 smoke test
 * (태스크 0698). phpunit 없이 `php` CLI만으로 실행된다.
 *
 * 실제 DB 없이 sqlite in-memory에 `db/schema/audit_event.sql`을 그대로
 * 적용해 (1) 이벤트가 없으면 빈 배열을 반환하는지, (2) occurred_at
 * 내림차순으로 정렬되는지, (3) limit이 상한(100)으로 capping되는지,
 * (4) actor_id가 null인 행도 그대로 조회되는지 확인한다
 * (0693 RecentDocumentsQueryTest.php와 동일한 방식).
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Audit\RecentAuditEventsQuery;

$failures = [];

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$auditEventSql = file_get_contents(__DIR__ . '/../../../../db/schema/audit_event.sql');
if ($auditEventSql === false) {
    fwrite(STDERR, "db/schema/audit_event.sql을 읽을 수 없습니다.\n");
    exit(1);
}
$connection->exec($auditEventSql);

/**
 * 지정된 occurred_at으로 audit_event row를 직접 삽입한다 (테스트 전용 helper).
 */
function insertAuditEvent(
    PDO $connection,
    string $id,
    string $category,
    string $action,
    string $entityId,
    ?string $actorId,
    string $occurredAt
): void {
    $statement = $connection->prepare(
        'INSERT INTO audit_event (id, category, action, entity_id, related_entity_id, actor_id, occurred_at) '
        . 'VALUES (:id, :category, :action, :entity_id, NULL, :actor_id, :occurred_at)'
    );
    $statement->execute([
        'id' => $id,
        'category' => $category,
        'action' => $action,
        'entity_id' => $entityId,
        'actor_id' => $actorId,
        'occurred_at' => $occurredAt,
    ]);
}

// ============================================================================
// (1) 이벤트가 없으면 빈 배열을 반환해야 한다.
// ============================================================================

$query = new RecentAuditEventsQuery($connection);
if ($query->listRecentEvents() !== []) {
    $failures[] = '이벤트가 없으면 빈 배열을 반환해야 한다.';
}

// ============================================================================
// (2) occurred_at 내림차순(최근 순)으로 정렬되어야 하고, actor_id가 null인
//     행도 그대로 조회되어야 한다.
// ============================================================================

insertAuditEvent($connection, 'evt-old', 'acl', 'rule_added', 'rule-1', 'user-1', '2026-01-01 00:00:00');
insertAuditEvent($connection, 'evt-new', 'discussion', 'thread_created', 'thread-1', null, '2026-06-01 00:00:00');
insertAuditEvent($connection, 'evt-mid', 'acl', 'rule_removed', 'rule-2', 'user-2', '2026-03-01 00:00:00');

$results = $query->listRecentEvents();
$ids = array_map(static fn ($event) => $event->id(), $results);

if ($ids !== ['evt-new', 'evt-mid', 'evt-old']) {
    $failures[] = 'listRecentEvents()는 occurred_at 내림차순으로 정렬해야 한다. 실제: ' . implode(', ', $ids);
}

if ($results[0]->actorId() !== null) {
    $failures[] = 'actor_id가 null인 행은 actorId()가 null을 반환해야 한다.';
}

if ($results[1]->category() !== 'acl' || $results[1]->action() !== 'rule_removed') {
    $failures[] = 'category/action이 저장된 값과 일치해야 한다.';
}

if ($results[2]->entityId() !== 'rule-1') {
    $failures[] = 'entityId()가 저장된 entity_id와 일치해야 한다.';
}

// ============================================================================
// (3) limit이 적용되어야 하고, MAX_LIMIT(100)을 넘는 값은 100으로 capping되어야 한다.
// ============================================================================

$limited = $query->listRecentEvents(2);
if (count($limited) !== 2) {
    $failures[] = 'listRecentEvents($limit)는 limit 개수만큼만 반환해야 한다.';
}
if ($limited[0]->id() !== 'evt-new' || $limited[1]->id() !== 'evt-mid') {
    $failures[] = 'limit이 적용되어도 정렬 순서는 유지되어야 한다.';
}

$cappedResults = $query->listRecentEvents(1000);
if (count($cappedResults) !== 3) {
    $failures[] = 'MAX_LIMIT을 넘는 요청도 실제 존재하는 행 수만큼만 반환해야 한다(여기서는 3건).';
}

if ($failures !== []) {
    fwrite(STDERR, "RecentAuditEventsQuery 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "RecentAuditEventsQuery 테스트 통과.\n");
exit(0);
