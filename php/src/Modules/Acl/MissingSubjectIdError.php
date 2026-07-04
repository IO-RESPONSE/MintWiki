<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 대상 종류가 USER 또는 GROUP인데 subject_id가 없을 때 발생 (태스크 0687).
 *
 * Python `MissingSubjectIdError`(src/modules/acl/rule.py)에 대응한다.
 */
final class MissingSubjectIdError extends \Exception
{
}
