<?php

declare(strict_types=1);

namespace MintWiki\Audit;

/**
 * 감사 이벤트를 기록하는 recorder 인터페이스 (태스크 0586).
 *
 * UI form action이 문서 생성/편집, 관리자 조치 등을 수행할 때,
 * 이 인터페이스를 구현한 recorder를 통해 AuditEvent를 기록한다.
 * 현재 단계에서는 NoOpAuditRecorder를 사용하여 placeholder 역할을 하며,
 * 이후 DatabaseAuditRepository가 이를 구현하여 실제 저장한다.
 */
interface AuditRecorder
{
    /**
     * 감사 이벤트를 기록한다.
     *
     * @param AuditEvent $event 기록할 감사 이벤트
     */
    public function record(AuditEvent $event): void;
}
