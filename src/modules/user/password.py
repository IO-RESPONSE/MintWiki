"""비밀번호 해시 인터페이스."""
from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """
    비밀번호 해시 및 검증의 인터페이스.

    구체적인 해시 알고리즘 구현(bcrypt, argon2 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    def hash(self, password: str) -> str:
        """
        평문 비밀번호를 해시한다.

        Args:
            password: 해시할 평문 비밀번호

        Returns:
            해시된 비밀번호 문자열
        """
        pass

    @abstractmethod
    def verify(self, password: str, hashed: str) -> bool:
        """
        평문 비밀번호가 해시된 비밀번호와 일치하는지 검증한다.

        Args:
            password: 검증할 평문 비밀번호
            hashed: 비교 대상이 되는 해시된 비밀번호

        Returns:
            일치하면 True, 아니면 False
        """
        pass
