<?php

declare(strict_types=1);

namespace MintWiki\Audit;

/**
 * `PdoAuditRecorder`가 `AuditEvent::metadata()`에서 entity_id를 찾지 못했을 때
 * 발생 (태스크 0714).
 *
 * `audit_event` 테이블의 `entity_id` 컬럼은 NOT NULL이라(`db/schema/audit_event.sql`)
 * 값이 없으면 INSERT 자체가 불가능하다. 다른 `Empty*Error` 클래스와 마찬가지로
 * 안정적인 error code(`docs/portable-exception-code-policy.md`) 부여는 이후
 * 태스크(0416 PHP error code registry)의 범위이므로 이 클래스도 CODE 상수 없이
 * 단순 예외로 둔다.
 */
final class MissingAuditEventEntityIdError extends \Exception
{
}
