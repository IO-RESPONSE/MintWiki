"""문서 저장소 인터페이스 및 구현."""
from abc import ABC, abstractmethod
from typing import Optional

from modules.document.model import Document


class DuplicateNormalizedTitleError(Exception):
    """정규화된 제목이 중복될 때 발생하는 예외."""

    pass


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


class InMemoryDocumentRepository(DocumentRepository):
    """
    메모리에 문서를 저장하는 저장소 구현.

    초기 테스트 및 개발 단계에서 사용하기 위한 메모리 기반
    저장소 구현이다. 정규화된 제목의 중복을 방지한다.
    """

    def __init__(self):
        """저장소를 초기화한다."""
        self.documents: dict[str, Document] = {}
        self.normalized_title_to_id: dict[str, str] = {}

    def create(self, document: Document) -> Document:
        """
        새로운 문서를 저장소에 저장한다.

        정규화된 제목이 이미 존재하면 DuplicateNormalizedTitleError를 발생시킨다.

        Args:
            document: 저장할 문서

        Returns:
            저장된 문서

        Raises:
            DuplicateNormalizedTitleError: 정규화된 제목이 중복된 경우
        """
        if document.normalized_title in self.normalized_title_to_id:
            raise DuplicateNormalizedTitleError(
                f"문서 제목 '{document.normalized_title}'는 이미 존재합니다"
            )

        self.documents[document.id] = document
        self.normalized_title_to_id[document.normalized_title] = document.id
        return document

    def get(self, id: str) -> Optional[Document]:
        """
        주어진 id로 문서를 조회한다.

        Args:
            id: 조회할 문서의 고유 식별자

        Returns:
            조회된 문서 또는 없으면 None
        """
        return self.documents.get(id)

    def get_by_normalized_title(self, normalized_title: str) -> Optional[Document]:
        """
        정규화된 제목으로 문서를 조회한다.

        Args:
            normalized_title: 조회할 문서의 정규화된 제목

        Returns:
            조회된 문서 또는 없으면 None
        """
        doc_id = self.normalized_title_to_id.get(normalized_title)
        if doc_id is None:
            return None
        return self.documents.get(doc_id)
