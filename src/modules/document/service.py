"""문서 생성 및 조회 서비스."""
import uuid
from typing import Optional

from modules.document.model import Document
from modules.document.repository import (
    DuplicateNormalizedTitleError,
    DocumentRepository,
)
from modules.document.title import EmptyTitleError, normalize_title
from modules.revision.repository import RevisionRepository
from modules.revision.service import RevisionService


class CurrentRevisionReadModel:
    """
    문서의 현재 리비전 정보를 포함하는 읽기 모델.

    문서의 메타데이터(제목, id)와 현재 리비전의 정보(리비전 id, 소스)를 함께 제공한다.
    """

    def __init__(
        self,
        title: str,
        document_id: str,
        revision_id: Optional[str],
        source: Optional[str],
    ):
        """
        읽기 모델을 생성한다.

        Args:
            title: 문서의 제목
            document_id: 문서의 고유 식별자
            revision_id: 현재 리비전의 id (리비전이 없으면 None)
            source: 현재 리비전의 소스 (리비전이 없으면 None)
        """
        self.title = title
        self.document_id = document_id
        self.revision_id = revision_id
        self.source = source


class DocumentService:
    """
    문서 생성 및 관리를 담당하는 서비스.

    문서 생성 시 제목을 정규화하고 저장소에 위임한다.
    문서 조회는 id 또는 제목으로 할 수 있다.
    소스가 제공되면 첫 리비전도 생성한다.
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        revision_repository: Optional[RevisionRepository] = None,
    ):
        """
        서비스를 초기화한다.

        Args:
            document_repository: 문서 저장소
            revision_repository: 리비전 저장소 (선택사항)
        """
        self.document_repository = document_repository
        self.revision_repository = revision_repository
        self.revision_service = (
            RevisionService(revision_repository)
            if revision_repository is not None
            else None
        )

    async def create(self, title: str, source: Optional[str] = None) -> Document:
        """
        새로운 문서를 생성한다.

        제목을 정규화하고 저장소에 위임하여 문서를 생성한다.
        소스가 제공되면 첫 리비전도 생성하고 document의 current_revision_id를
        설정한 후 데이터베이스에 저장한다.

        Args:
            title: 문서의 제목
            source: 문서의 초기 소스 텍스트 (선택사항)

        Returns:
            생성된 문서

        Raises:
            EmptyTitleError: 제목이 비어있거나 공백만 있는 경우
            DuplicateNormalizedTitleError: 정규화된 제목이 중복된 경우
        """
        document = Document(id=str(uuid.uuid4()), title=title)
        document = await self.document_repository.create(document)

        if source is not None and self.revision_service is not None:
            revision = await self.revision_service.create(
                document_id=document.id,
                source=source,
                author_id="",
                summary="",
            )
            document.current_revision_id = revision.id
            document = await self.document_repository.update(document)

        return document

    async def get(self, id: str) -> Optional[Document]:
        """
        주어진 id로 문서를 조회한다.

        id에 해당하는 문서가 없으면 None을 반환한다.

        Args:
            id: 조회할 문서의 고유 식별자

        Returns:
            조회된 문서 또는 없으면 None
        """
        return await self.document_repository.get(id)

    async def get_by_title(self, title: str) -> Optional[Document]:
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
        return await self.document_repository.get_by_normalized_title(normalized)

    async def get_current_revision_read_model(
        self, document_id: str
    ) -> Optional[CurrentRevisionReadModel]:
        """
        문서의 현재 리비전 읽기 모델을 조회한다.

        문서 id로 문서를 조회하고, 현재 리비전이 있으면 그 정보를 포함하는
        읽기 모델을 반환한다. 현재 리비전이 없으면 revision_id와 source는 None이다.

        Args:
            document_id: 조회할 문서의 고유 식별자

        Returns:
            현재 리비전 읽기 모델 또는 문서가 없으면 None

        Raises:
            리비전 저장소가 없거나 현재 리비전 id는 있지만 리비전을 찾을 수 없으면
            현재 리비전 정보는 None으로 처리한다.
        """
        document = await self.document_repository.get(document_id)
        if document is None:
            return None

        source = None
        if (
            document.current_revision_id is not None
            and self.revision_service is not None
        ):
            revision = await self.revision_service.get(document.current_revision_id)
            if revision is not None:
                source = revision.source

        return CurrentRevisionReadModel(
            title=document.title,
            document_id=document.id,
            revision_id=document.current_revision_id,
            source=source,
        )
