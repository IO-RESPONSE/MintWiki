"""문서 생성 및 조회 서비스."""
import uuid
from typing import Optional

from modules.document.model import Document
from modules.document.repository import (
    DuplicateNormalizedTitleError,
    DocumentRepository,
)
from modules.document.title import EmptyTitleError, normalize_title


class DocumentService:
    """
    문서 생성 및 관리를 담당하는 서비스.

    문서 생성 시 제목을 정규화하고 저장소에 위임한다.
    문서 조회는 id 또는 제목으로 할 수 있다.
    """

    def __init__(self, repository: DocumentRepository):
        """
        서비스를 초기화한다.

        Args:
            repository: 문서 저장소
        """
        self.repository = repository

    def create(self, title: str) -> Document:
        """
        새로운 문서를 생성한다.

        제목을 정규화하고 저장소에 위임하여 문서를 생성한다.

        Args:
            title: 문서의 제목

        Returns:
            생성된 문서

        Raises:
            EmptyTitleError: 제목이 비어있거나 공백만 있는 경우
            DuplicateNormalizedTitleError: 정규화된 제목이 중복된 경우
        """
        document = Document(id=str(uuid.uuid4()), title=title)
        return self.repository.create(document)

    def get(self, id: str) -> Optional[Document]:
        """
        주어진 id로 문서를 조회한다.

        id에 해당하는 문서가 없으면 None을 반환한다.

        Args:
            id: 조회할 문서의 고유 식별자

        Returns:
            조회된 문서 또는 없으면 None
        """
        return self.repository.get(id)

    def get_by_title(self, title: str) -> Optional[Document]:
        """
        주어진 제목으로 문서를 조회한다.

        제목을 정규화하여 저장소에서 조회한다.
        제목에 해당하는 문서가 없으면 None을 반환한다.

        Args:
            title: 조회할 문서의 제목

        Returns:
            조회된 문서 또는 없으면 None

        Raises:
            EmptyTitleError: 제목이 비어있거나 공백만 있는 경우
        """
        normalized = normalize_title(title)
        return self.repository.get_by_normalized_title(normalized)
