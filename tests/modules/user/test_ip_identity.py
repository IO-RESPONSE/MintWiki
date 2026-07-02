"""IP 아이덴티티 모델 테스트."""
import pytest
from modules.user.ip_identity import InvalidIpAddressError, IpIdentity


class TestIpIdentityConstruction:
    """IP 아이덴티티 생성 테스트."""

    def test_creates_ip_identity_with_ipv4_address(self):
        """IPv4 주소로 IP 아이덴티티를 생성한다."""
        identity = IpIdentity("192.168.0.1")
        assert identity.ip_address == "192.168.0.1"

    def test_creates_ip_identity_with_ipv6_address(self):
        """IPv6 주소로 IP 아이덴티티를 생성한다."""
        identity = IpIdentity("2001:db8::1")
        assert identity.ip_address == "2001:db8::1"

    def test_is_anonymous_flag_is_true(self):
        """is_anonymous 플래그가 True로 설정된다."""
        identity = IpIdentity("192.168.0.1")
        assert identity.is_anonymous is True

    def test_each_instance_is_distinct(self):
        """IP 아이덴티티 인스턴스는 서로 다른 객체이다."""
        first = IpIdentity("192.168.0.1")
        second = IpIdentity("192.168.0.1")
        assert first is not second

    def test_rejects_invalid_ip_address(self):
        """올바르지 않은 형식의 IP 주소는 거부한다."""
        with pytest.raises(InvalidIpAddressError):
            IpIdentity("not-an-ip")

    def test_rejects_empty_ip_address(self):
        """빈 문자열은 IP 주소로 허용하지 않는다."""
        with pytest.raises(InvalidIpAddressError):
            IpIdentity("")
