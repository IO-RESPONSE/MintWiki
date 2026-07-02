"""익명 아이덴티티 모델 테스트."""
from modules.user.anonymous import AnonymousIdentity


class TestAnonymousIdentity:
    """익명 아이덴티티 생성 및 속성 테스트."""

    def test_creates_anonymous_identity_without_arguments(self):
        """인자 없이 익명 아이덴티티를 생성한다."""
        identity = AnonymousIdentity()
        assert identity is not None

    def test_is_anonymous_flag_is_true(self):
        """is_anonymous 플래그가 True로 설정된다."""
        identity = AnonymousIdentity()
        assert identity.is_anonymous is True

    def test_each_instance_is_distinct(self):
        """익명 아이덴티티 인스턴스는 서로 다른 객체이다."""
        first = AnonymousIdentity()
        second = AnonymousIdentity()
        assert first is not second
