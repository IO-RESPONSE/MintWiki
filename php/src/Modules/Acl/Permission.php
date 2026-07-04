<?php

declare(strict_types=1);

namespace MintWiki\Acl;

/**
 * 문서에 대해 검사할 수 있는 권한 종류 (태스크 0687).
 *
 * Python `Permission`(src/modules/acl/permission.py)과 값을 맞춘다.
 */
enum Permission: string
{
    case Read = 'read';
    case Edit = 'edit';
    case Discuss = 'discuss';
    case Move = 'move';
    case Delete = 'delete';
    case Admin = 'admin';
}
