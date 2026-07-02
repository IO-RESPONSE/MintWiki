<?php

declare(strict_types=1);

namespace MintWiki\User;

/**
 * IP 주소 형식이 올바르지 않을 때 발생 (태스크 0409).
 *
 * Python `InvalidIpAddressError`(src/modules/user/ip_identity.py)에
 * 대응한다. EmptyUsernameError와 같은 이유로 CODE 상수는 아직 두지 않는다.
 */
final class InvalidIpAddressError extends \Exception
{
}
