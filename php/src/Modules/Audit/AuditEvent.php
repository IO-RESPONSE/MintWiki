<?php

declare(strict_types=1);

namespace MintWiki\Audit;

/**
 * 감사 이벤트를 표현하는 불변 value object (태스크 0413).
 *
 * audit 모듈은 Python 쪽에 아직 서비스/이벤트 모델 구현이 없다 —
 * src/modules/audit 에는 README.md 와 manifest.json 만 존재하며(태스크
 * 0363), 이벤트 모델 자체는 이후 Python 태스크(0342 add-audit-event-model,
 * 아직 큐에 있음)가 구현할 목표다. 그래서 이 클래스는 기존 Python 클래스를
 * 1:1로 옮긴 포트가 아니라, `src/modules/audit/manifest.json` 의
 * contract_notes 가 이미 고정한 계약 — record() 가 유일한 쓰기 경로이고
 * 한 번 기록된 이벤트는 이후 어떤 호출로도 수정되거나 삭제될 수 없다는
 * append-only 원칙 — 을 PHP value object 수준에서 먼저 굳힌 것이다.
 *
 * acl/discussion 모듈이 이미 갖고 있는 자체 AclAuditEvent
 * (src/modules/acl/audit_event.py)/DiscussionAuditEvent
 * (src/modules/discussion/audit_event.py)는 각자 모듈 전용 action enum과
 * 필드를 쓰는 별개 모델이며, 이 클래스가 대체하지 않는다. 이 클래스는
 * manifest 와 docs/modules.md 가 audit 의 책임으로 명시한 "document,
 * permission, admin, auth, and job logs"를 모두 아우르는 중앙 audit
 * 모듈의 범용 이벤트이며, module/action 필드를 문자열로 두어 어떤 도메인
 * 모듈이 기록한 이벤트든 담을 수 있게 한다.
 *
 * append-only 계약은 이 클래스에서 모든 필드를 readonly 로 두고 mutator
 * 메서드를 하나도 두지 않는 방식으로 표현한다 — 한 번 생성된 AuditEvent
 * 인스턴스는 어떤 메서드 호출로도 값이 바뀌지 않는다(Discussion\Comment
 * 의 hide() 같은 이후 변경 메서드가 없다). 이벤트를 실제로 저장소에
 * append 하는 책임(record())과 조회하는 책임(list_events)은 이 모델이
 * 아닌 이후 태스크의 audit 서비스/저장소 포트가 담당한다.
 */
final class AuditEvent
{
    /**
     * @param array<string, mixed> $metadata
     */
    public function __construct(
        private readonly string $id,
        private readonly string $module,
        private readonly string $action,
        private readonly \DateTimeImmutable $occurredAt,
        private readonly ?string $actorId = null,
        private readonly array $metadata = []
    ) {
        if (trim($id) === '') {
            throw new EmptyAuditEventIdError('감사 이벤트 id는 비어있을 수 없습니다');
        }
        if (trim($module) === '') {
            throw new EmptyAuditEventModuleError('감사 이벤트를 기록한 모듈 이름은 비어있을 수 없습니다');
        }
        if (trim($action) === '') {
            throw new EmptyAuditEventActionError('감사 이벤트 action은 비어있을 수 없습니다');
        }
    }

    public function id(): string
    {
        return $this->id;
    }

    public function module(): string
    {
        return $this->module;
    }

    public function action(): string
    {
        return $this->action;
    }

    public function occurredAt(): \DateTimeImmutable
    {
        return $this->occurredAt;
    }

    public function actorId(): ?string
    {
        return $this->actorId;
    }

    /**
     * @return array<string, mixed>
     */
    public function metadata(): array
    {
        return $this->metadata;
    }
}
