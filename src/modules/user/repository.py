"""사용자 저장소 인터페이스 및 구현."""
from abc import ABC, abstractmethod
from typing import Optional

from modules.user.model import User


class UserRepository(ABC):
    """
    사용자 저장소의 인터페이스.

    저장소는 사용자를 저장하고 검색하는 메서드를 정의한다.
    구체적인 저장소 구현(메모리, 데이터베이스 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def create(self, user: User) -> User:
        """
        새로운 사용자를 저장소에 저장한다.

        Args:
            user: 저장할 사용자

        Returns:
            저장된 사용자

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[User]:
        """
        주어진 id로 사용자를 조회한다.

        Args:
            id: 조회할 사용자의 고유 식별자

        Returns:
            조회된 사용자 또는 없으면 None
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        주어진 사용자명으로 사용자를 조회한다.

        Args:
            username: 조회할 사용자의 사용자명

        Returns:
            조회된 사용자 또는 없으면 None
        """
        pass


class InMemoryUserRepository(UserRepository):
    """
    메모리에 사용자를 저장하는 저장소 구현.

    초기 테스트 및 개발 단계에서 사용하기 위한 메모리 기반
    저장소 구현이다.
    """

    def __init__(self):
        """저장소를 초기화한다."""
        self.users: dict[str, User] = {}
        self.username_to_id: dict[str, str] = {}

    async def create(self, user: User) -> User:
        """
        새로운 사용자를 저장소에 저장한다.

        Args:
            user: 저장할 사용자

        Returns:
            저장된 사용자
        """
        self.users[user.id] = user
        self.username_to_id[user.username] = user.id
        return user

    async def get(self, id: str) -> Optional[User]:
        """
        주어진 id로 사용자를 조회한다.

        Args:
            id: 조회할 사용자의 고유 식별자

        Returns:
            조회된 사용자 또는 없으면 None
        """
        return self.users.get(id)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        주어진 사용자명으로 사용자를 조회한다.

        Args:
            username: 조회할 사용자의 사용자명

        Returns:
            조회된 사용자 또는 없으면 None
        """
        user_id = self.username_to_id.get(username)
        if user_id is None:
            return None
        return self.users.get(user_id)
