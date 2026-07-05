<?php

declare(strict_types=1);

/**
 * `MintWiki\Audit\PdoAuditRecorder`(태스크 0714)의 동작을 확인하는 smoke test.
 * phpunit 없이 `php` CLI만으로 실행된다(0698 RecentAuditEventsQueryTest.php와
 * 동일한 방식) — 실제 DB 없이 sqlite in-memory에 `db/schema/audit_event.sql`을
 * 그대로 적용한다.
 *
 * 검증 대상:
 * (1) record()가 `audit_event` 테이블에 INSERT하고, `RecentAuditEventsQuery`로
 *     그대로 조회된다(컬럼 매핑: module→category, actorId→actor_id,
 *     metadata['entity_id']→entity_id, metadata['related_entity_id']→
 *     related_entity_id).
 * (2) related_entity_id/actorId가 없는 이벤트도 null로 저장된다.
 * (3) occurred_at은 이벤트의 시간대와 무관하게 UTC로 정규화되어 저장된다.
 * (4) metadata에 entity_id가 없으면 MissingAuditEventEntityIdError를 던지고,
 *     아무 행도 저장되지 않는다.
 */

$autoloadFile = __DIR__ . '/../../../vendor/autoload.php';

if (!is_file($autoloadFile)) {
    fwrite(STDERR, "vendor/autoload.php를 찾을 수 없습니다. php/ 디렉터리에서 `composer install`을 먼저 실행하세요.\n");
    exit(1);
}

require $autoloadFile;

use MintWiki\Audit\AuditEvent;
use MintWiki\Audit\MissingAuditEventEntityIdError;
use MintWiki\Audit\PdoAuditRecorder;
use MintWiki\Audit\RecentAuditEventsQuery;

$failures = [];

$auditEventSql = file_get_contents(__DIR__ . '/../../../../db/schema/audit_event.sql');
if ($auditEventSql === false) {
    fwrite(STDERR, "db/schema/audit_event.sql을 읽을 수 없습니다.\n");
    exit(1);
}

$connection = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$connection->exec($auditEventSql);

$recorder = new PdoAuditRecorder($connection);
$query = new RecentAuditEventsQuery($connection);

// ============================================================================
// (1) record()가 저장하고, RecentAuditEventsQuery로 그대로 조회되어야 한다.
// ============================================================================

$recorder->record(new AuditEvent(
    'evt-doc-created',
    'document',
    'created',
    new \DateTimeImmutable('2026-03-01T09:00:00+09:00'),
    'user-1',
    ['entity_id' => 'doc-1', 'related_entity_id' => 'rev-1']
));

$events = $query->listRecentEvents();
if (count($events) !== 1) {
    $failures[] = 'record() 이후 조회되는 이벤트는 1건이어야 하는데 ' . count($events) . '건이었다.';
} else {
    $event = $events[0];
    if ($event->id() !== 'evt-doc-created') {
        $failures[] = 'id가 저장한 값과 일치해야 한다.';
    }
    if ($event->category() !== 'document') {
        $failures[] = 'category는 AuditEvent::module()의 값으로 저장되어야 한다.';
    }
    if ($event->action() !== 'created') {
        $failures[] = 'action이 저장한 값과 일치해야 한다.';
    }
    if ($event->entityId() !== 'doc-1') {
        $failures[] = 'entity_id는 metadata[entity_id]의 값으로 저장되어야 한다.';
    }
    if ($event->relatedEntityId() !== 'rev-1') {
        $failures[] = 'related_entity_id는 metadata[related_entity_id]의 값으로 저장되어야 한다.';
    }
    if ($event->actorId() !== 'user-1') {
        $failures[] = 'actor_id는 AuditEvent::actorId()의 값으로 저장되어야 한다.';
    }

    // ------------------------------------------------------------------
    // (3) occurred_at은 UTC로 정규화되어야 한다 (입력은 +09:00 09:00 → UTC 00:00).
    // ------------------------------------------------------------------
    if (!str_starts_with($event->occurredAt(), '2026-03-01 00:00:00')) {
        $failures[] = 'occurred_at은 UTC로 정규화되어 저장되어야 하는데 "' . $event->occurredAt() . '"이었다.';
    }
}

// ============================================================================
// (2) related_entity_id/actorId가 없는 이벤트도 null로 저장되어야 한다.
// ============================================================================

$recorder->record(new AuditEvent(
    'evt-logout',
    'auth',
    'logout',
    new \DateTimeImmutable('2026-03-02T00:00:00+00:00'),
    null,
    ['entity_id' => 'account-1']
));

$eventsAfterSecond = $query->listRecentEvents();
$logoutEvent = null;
foreach ($eventsAfterSecond as $candidate) {
    if ($candidate->id() === 'evt-logout') {
        $logoutEvent = $candidate;
    }
}
if ($logoutEvent === null) {
    $failures[] = 'related_entity_id/actorId가 없는 이벤트도 저장되어 조회되어야 한다.';
} else {
    if ($logoutEvent->relatedEntityId() !== null) {
        $failures[] = 'metadata에 related_entity_id가 없으면 null로 저장되어야 한다.';
    }
    if ($logoutEvent->actorId() !== null) {
        $failures[] = 'AuditEvent::actorId()가 null이면 actor_id도 null로 저장되어야 한다.';
    }
}

// ============================================================================
// (4) metadata에 entity_id가 없으면 예외를 던지고 아무 행도 저장하면 안 된다.
// ============================================================================

$countBeforeFailure = count($query->listRecentEvents());
try {
    $recorder->record(new AuditEvent(
        'evt-missing-entity',
        'document',
        'created',
        new \DateTimeImmutable('now')
    ));
    $failures[] = 'metadata에 entity_id가 없으면 MissingAuditEventEntityIdError를 던져야 한다.';
} catch (MissingAuditEventEntityIdError $e) {
    // 예상된 동작.
}
$countAfterFailure = count($query->listRecentEvents());
if ($countAfterFailure !== $countBeforeFailure) {
    $failures[] = 'entity_id가 없어 예외가 발생하면 어떤 행도 저장되면 안 된다.';
}

if ($failures !== []) {
    fwrite(STDERR, "PdoAuditRecorder 테스트 실패:\n");
    foreach ($failures as $failure) {
        fwrite(STDERR, " - {$failure}\n");
    }
    exit(1);
}

fwrite(STDOUT, "PdoAuditRecorder 테스트 통과.\n");
exit(0);
