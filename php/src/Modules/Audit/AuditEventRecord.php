<?php

declare(strict_types=1);

namespace MintWiki\Audit;

/**
 * `audit_event` 테이블 한 행을 그대로 옮긴 읽기 전용 value object (태스크 0698).
 *
 * `AuditEvent`(태스크 0413)는 module/action/metadata 필드를 갖는, 아직 어떤
 * recorder도 실제로 쓰지 않는(NoOpAuditRecorder만 존재) 미래 지향 모델이라
 * 실제 테이블 컬럼(category/action/entity_id/related_entity_id/actor_id/
 * occurred_at, db/schema/audit_event.sql)과 이름·구조가 다르다. 이 클래스는
 * `RecentAuditEventsQuery`가 조회한 실제 컬럼값을 그대로 담아 `AuditViewerPage`에
 * 전달하는 용도로 한정한다.
 */
final class AuditEventRecord
{
    public function __construct(
        private readonly string $id,
        private readonly string $category,
        private readonly string $action,
        private readonly string $entityId,
        private readonly ?string $relatedEntityId,
        private readonly ?string $actorId,
        private readonly string $occurredAt
    ) {
    }

    public function id(): string
    {
        return $this->id;
    }

    public function category(): string
    {
        return $this->category;
    }

    public function action(): string
    {
        return $this->action;
    }

    public function entityId(): string
    {
        return $this->entityId;
    }

    public function relatedEntityId(): ?string
    {
        return $this->relatedEntityId;
    }

    public function actorId(): ?string
    {
        return $this->actorId;
    }

    public function occurredAt(): string
    {
        return $this->occurredAt;
    }
}
