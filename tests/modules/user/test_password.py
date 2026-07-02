"""비밀번호 해시 인터페이스 테스트."""
import pytest

from modules.user.password import PasswordHasher


class TestPasswordHasherInterface:
    """비밀번호 해시 인터페이스 테스트."""

    def test_password_hasher_is_abstract(self):
        """비밀번호 해셔는 추상 클래스이다."""
        with pytest.raises(TypeError):
            PasswordHasher()

    def test_hash_method_exists(self):
        """비밀번호 해셔는 hash 메서드를 정의한다."""
        assert hasattr(PasswordHasher, "hash")

    def test_verify_method_exists(self):
        """비밀번호 해셔는 verify 메서드를 정의한다."""
        assert hasattr(PasswordHasher, "verify")

    def test_concrete_subclass_must_implement_hash_and_verify(self):
        """구체 구현체는 hash와 verify를 모두 구현해야 한다."""

        class IncompletePasswordHasher(PasswordHasher):
            def hash(self, password: str) -> str:
                return password

        with pytest.raises(TypeError):
            IncompletePasswordHasher()

    def test_concrete_subclass_can_be_instantiated(self):
        """hash와 verify를 모두 구현하면 인스턴스화할 수 있다."""

        class EchoPasswordHasher(PasswordHasher):
            def hash(self, password: str) -> str:
                return f"hashed:{password}"

            def verify(self, password: str, hashed: str) -> bool:
                return f"hashed:{password}" == hashed

        hasher = EchoPasswordHasher()
        hashed = hasher.hash("secret")
        assert hashed == "hashed:secret"
        assert hasher.verify("secret", hashed) is True
        assert hasher.verify("wrong", hashed) is False
