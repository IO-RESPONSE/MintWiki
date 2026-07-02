"""문서 보호 저장소 인터페이스."""
from abc import ABC, abstractmethod
from typing import Optional

from modules.document.protection import Protection


class ProtectionRepository(ABC):
    """
    문서 보호를 저장하고 조회하는 저장소 인터페이스.

    구현체는 보호 데이터를 생성, 조회, 삭제하는 메서드를 제공해야 한다.
    """

    @abstractmethod
    async def create(self, protection: Protection) -> Protection:
        """
        새로운 문서 보호를 저장소에 저장한다.

        Args:
            protection: 저장할 보호

        Returns:
            저장된 보호
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Protection]:
        """
        id로 보호를 조회한다.

        Args:
            id: 조회할 보호의 id

        Returns:
            보호가 존재하면 Protection 객체, 없으면 None
        """
        pass

    @abstractmethod
    async def get_by_document_id(self, document_id: str) -> Optional[Protection]:
        """
        문서 id로 보호를 조회한다.

        Args:
            document_id: 조회할 문서의 id

        Returns:
            보호가 존재하면 Protection 객체, 없으면 None
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        """
        id로 보호를 삭제한다.

        Args:
            id: 삭제할 보호의 id
        """
        pass
