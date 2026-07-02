<?php

declare(strict_types=1);

namespace MintWiki\Audit;

/**
 * 감사 이벤트 id가 비어있거나 공백만 있을 때 발생 (태스크 0413).
 *
 * Python 쪽에는 아직 대응하는 audit 이벤트 모델 자체가 없다(위
 * AuditEvent 클래스 문서 참고). 다른 모듈의 Empty*Error 클래스와
 * 마찬가지로 안정적인 error code(`docs/portable-exception-code-policy.md`)
 * 부여는 이후 태스크(0416 PHP error code registry)의 범위이므로, 이
 * 클래스도 CODE 상수 없이 단순 예외로 둔다.
 */
final class EmptyAuditEventIdError extends \Exception
{
}
