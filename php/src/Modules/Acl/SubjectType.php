<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * ACL 규칙이 적용되는 대상의 종류 (태스크 0687).
 *
 * Python `SubjectType`(src/modules/acl/rule.py)과 값을 맞춘다.
 */
enum SubjectType: string
{
    case User = 'user';
    case Group = 'group';
    case Anonymous = 'anonymous';
    case All = 'all';
}
