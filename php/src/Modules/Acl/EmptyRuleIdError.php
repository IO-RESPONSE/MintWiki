<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 규칙 id가 비어있을 때 발생 (태스크 0687).
 *
 * Python `EmptyRuleIdError`(src/modules/acl/rule.py)에 대응한다.
 */
final class EmptyRuleIdError extends \Exception
{
}
