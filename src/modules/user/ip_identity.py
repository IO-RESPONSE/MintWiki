"""IP 아이덴티티 도메인 모델."""
import ipaddress


class InvalidIpAddressError(Exception):
    """IP 주소 형식이 올바르지 않을 때 발생."""

    pass


class IpIdentity:
    """
    로그인하지 않고 IP 주소만으로 식별되는 방문자를 나타내는 도메인 모델.

    AnonymousIdentity와 달리 방문자를 구분할 수 있는 IP 주소를 가지며,
    IP 기반 권한 검사나 차단 규칙에서 식별자로 사용된다.
    """

    is_anonymous = True

    def __init__(self, ip_address: str):
        """
        IP 아이덴티티를 생성한다.

        Args:
            ip_address: 방문자를 식별하는 IP 주소 (IPv4 또는 IPv6)

        Raises:
            InvalidIpAddressError: IP 주소 형식이 올바르지 않은 경우
        """
        try:
            ipaddress.ip_address(ip_address)
        except ValueError as exc:
            raise InvalidIpAddressError(
                f"올바르지 않은 IP 주소입니다: {ip_address!r}"
            ) from exc

        self.ip_address = ip_address

    def __repr__(self) -> str:
        return f"IpIdentity(ip_address={self.ip_address!r})"
