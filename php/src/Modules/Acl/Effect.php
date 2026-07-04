<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 규칙이 권한을 허용하는지 거부하는지를 나타낸다 (태스크 0687).
 *
 * Python `Effect`(src/modules/acl/rule.py)와 값을 맞춘다.
 */
enum Effect: string
{
    case Allow = 'allow';
    case Deny = 'deny';
}
