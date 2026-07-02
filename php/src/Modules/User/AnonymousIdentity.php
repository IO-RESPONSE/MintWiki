<?php

declare(strict_types=1);

namespace MintWiki\User;

/**
 * 로그인하지 않은 방문자를 표현하는 value object (태스크 0409).
 *
 * Python `AnonymousIdentity`(src/modules/user/anonymous.py)에 대응한다.
 * User와 달리 계정 식별자나 사용자명을 가지지 않으며, isAnonymous()는
 * 항상 true를 반환한다 — 권한 검사에서 로그인 여부를 구분하는 표식이다.
 * IpIdentity와 달리 방문자를 구분할 수 있는 IP 주소도 갖지 않는다.
 */
final class AnonymousIdentity
{
    public function isAnonymous(): bool
    {
        return true;
    }
}
