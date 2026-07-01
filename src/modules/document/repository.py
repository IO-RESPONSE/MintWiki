"""문서 저장소 인터페이스."""
from abc import ABC, abstractmethod
from typing import Optional

from modules.document.model import Document


class DocumentRepository(ABC):
    """
    문서 저장소의 인터페이스.

    저장소는 문서를 저장하고 검색하는 메서드를 정의한다.
    구체적인 저장소 구현(메모리, 데이터베이스 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    def create(self, document: Document) -> Document:
        """
        새로운 문서를 저장소에 저장한다.

        Args:
            document: 저장할 문서

        Returns:
            저장된 문서

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[Document]:
        """
        주어진 id로 문서를 조회한다.

        Args:
            id: 조회할 문서의 고유 식별자

        Returns:
            조회된 문서 또는 없으면 None
        """
        pass

    @abstractmethod
    def get_by_normalized_title(self, normalized_title: str) -> Optional[Document]:
        """
        정규화된 제목으로 문서를 조회한다.

        Args:
            normalized_title: 조회할 문서의 정규화된 제목

        Returns:
            조회된 문서 또는 없으면 None
        """
        pass
