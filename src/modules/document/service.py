"""문서 생성 서비스."""
import uuid

from modules.document.model import Document
from modules.document.repository import (
    DuplicateNormalizedTitleError,
    DocumentRepository,
)
from modules.document.title import EmptyTitleError


class DocumentService:
    """
    문서 생성 및 관리를 담당하는 서비스.

    문서 생성 시 제목을 정규화하고 저장소에 위임한다.
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
