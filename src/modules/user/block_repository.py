"""차단 저장소 인터페이스."""
from abc import ABC, abstractmethod
from typing import Optional

from modules.user.block import Block


class BlockRepository(ABC):
    """
    차단 저장소의 인터페이스.

    저장소는 차단을 저장하고 검색하고 삭제하는 메서드를 정의한다.
    구체적인 저장소 구현(메모리, 데이터베이스 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def create(self, block: Block) -> Block:
        """
        새로운 차단을 저장소에 저장한다.

        Args:
            block: 저장할 차단

        Returns:
            저장된 차단

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Block]:
        """
        주어진 id로 차단을 조회한다.

        Args:
            id: 조회할 차단의 고유 식별자

        Returns:
            조회된 차단 또는 없으면 None
        """
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[Block]:
        """
        주어진 사용자 id로 차단을 조회한다.

        Args:
            user_id: 조회할 차단 대상 사용자의 id

        Returns:
            조회된 차단 또는 없으면 None
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        """
        주어진 id의 차단을 저장소에서 삭제한다.

        Args:
            id: 삭제할 차단의 고유 식별자
        """
        pass
