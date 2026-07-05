<?php

declare(strict_types=1);

namespace MintWiki\Audit;

use PDO;

/**
 * `AuditRecorder` 포트의 PDO 구현체 (태스크 0714).
 *
 * `db/schema/audit_event.sql`의 `audit_event` 테이블에 실제로 INSERT하는 첫
 * recorder다 — 이전까지는 `NoOpAuditRecorder`만 있어 `/admin/audit` 뷰어(0698
 * `RecentAuditEventsQuery`)가 항상 빈 상태였다.
 *
 * `Revision\PdoRepository`(태스크 0685)와 동일한 관례를 따른다 — 명시적 컬럼
 * 목록으로 INSERT하고, occurred_at은 저장 직전 UTC로 정규화한다(`[Portable
 * Timestamp Column Policy]`).
 *
 * `AuditEvent`(태스크 0413)의 `module`/`action`/`actorId`/`occurredAt`은 테이블의
 * `category`/`action`/`actor_id`/`occurred_at` 컬럼에 그대로 대응하지만, 테이블은
 * `entity_id`(NOT NULL)와 `related_entity_id`(nullable) 다형 참조 컬럼을 추가로
 * 요구한다(`AuditEventRecord` 참고). `AuditEvent`는 아직 이 두 필드를 전용
 * 프로퍼티로 갖지 않으므로, 호출자가 `metadata`에 `entity_id`(필수)/
 * `related_entity_id`(선택) 키로 채워 넣는 관례를 이 recorder가 읽어 매핑한다.
 * `entity_id`가 없으면 append 자체가 불가능한 스키마 위반이므로
 * `MissingAuditEventEntityIdError`를 던진다 — 호출자는(기존
 * `DocumentCreateHandler` 예시처럼) record() 호출을 try/catch로 감싸 감사 기록
 * 실패가 요청을 깨뜨리지 않게 해야 한다.
 */
final class PdoAuditRecorder implements AuditRecorder
{
    public function __construct(private readonly PDO $connection)
    {
    }

    public function record(AuditEvent $event): void
    {
        $metadata = $event->metadata();

        $entityId = $metadata['entity_id'] ?? null;
        if (!is_string($entityId) || trim($entityId) === '') {
            throw new MissingAuditEventEntityIdError(
                '감사 이벤트 metadata에 entity_id가 없습니다: module=' . $event->module() . ', action=' . $event->action()
            );
        }

        $relatedEntityId = $metadata['related_entity_id'] ?? null;

        $statement = $this->connection->prepare(
            'INSERT INTO audit_event (id, category, action, entity_id, related_entity_id, actor_id, occurred_at) '
            . 'VALUES (:id, :category, :action, :entity_id, :related_entity_id, :actor_id, :occurred_at)'
        );

        $statement->execute([
            'id' => $event->id(),
            'category' => $event->module(),
            'action' => $event->action(),
            'entity_id' => $entityId,
            'related_entity_id' => $relatedEntityId === null ? null : (string) $relatedEntityId,
            'actor_id' => $event->actorId(),
            'occurred_at' => $event->occurredAt()->setTimezone(new \DateTimeZone('UTC'))->format('Y-m-d H:i:s'),
        ]);
    }
}
