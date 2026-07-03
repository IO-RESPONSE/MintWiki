<?php

declare(strict_types=1);

namespace MintWiki\Audit;

/**
 * 아무 작업도 하지 않는 no-op audit recorder (태스크 0586).
 *
 * Phase D 초반에는 UI handler들이 audit hook을 호출하는 위치를 확보하되,
 * 실제 저장은 하지 않는다. 이 구현체는 record() 호출을 무시한다.
 * 이후 DatabaseAuditRepository가 AuditRecorder 인터페이스를 구현하여
 * 실제 감사 이벤트를 저장소에 기록한다 — handler 코드는 변경하지 않고
 * 의존성 주입 시점에 구현체만 교체된다.
 */
final class NoOpAuditRecorder implements AuditRecorder
{
    /**
     * 감사 이벤트를 무시한다.
     */
    public function record(AuditEvent $event): void
    {
        // 현재 단계에서는 아무 작업도 하지 않음
    }
}
