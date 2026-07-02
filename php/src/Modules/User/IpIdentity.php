<?php

declare(strict_types=1);

namespace MintWiki\User;

/**
 * 로그인하지 않고 IP 주소만으로 식별되는 방문자를 표현하는 value object
 * (태스크 0409).
 *
 * Python `IpIdentity`(src/modules/user/ip_identity.py)에 대응한다.
 * AnonymousIdentity와 달리 방문자를 구분할 수 있는 IP 주소(IPv4 또는
 * IPv6)를 가지며, 형식이 올바르지 않으면 InvalidIpAddressError를 던진다.
 * isAnonymous()는 AnonymousIdentity와 마찬가지로 항상 true를 반환한다.
 */
final class IpIdentity
{
    private readonly string $ipAddress;

    public function __construct(string $ipAddress)
    {
        if (filter_var($ipAddress, FILTER_VALIDATE_IP) === false) {
            throw new InvalidIpAddressError("올바르지 않은 IP 주소입니다: '{$ipAddress}'");
        }

        $this->ipAddress = $ipAddress;
    }

    public function ipAddress(): string
    {
        return $this->ipAddress;
    }

    public function isAnonymous(): bool
    {
        return true;
    }
}
