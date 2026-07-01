"""리비전 생성 및 조회 서비스."""
import uuid
from typing import Optional

from modules.revision.model import Revision
from modules.revision.repository import RevisionRepository


class RevisionService:
    """
    리비전 생성 및 관리를 담당하는 서비스.

    리비전 생성 시 id를 생성하고 저장소에 위임한다.
    리비전 조회는 id 또는 문서 id로 할 수 있다.
    """

    def __init__(self, repository: RevisionRepository):
        """
        서비스를 초기화한다.

        Args:
            repository: 리비전 저장소
        """
        self.repository = repository

    def create(
        self,
        document_id: str,
        source: str,
        author_id: str,
        summary: str,
        parent_revision_id: Optional[str] = None,
    ) -> Revision:
        """
        새로운 리비전을 생성한다.

        문서 id, 소스, 저자 id, 요약을 받아 리비전을 생성한다.

        Args:
            document_id: 리비전이 속한 문서의 id
            source: 리비전의 소스 텍스트
            author_id: 저자의 id
            summary: 편집 요약
            parent_revision_id: 부모 리비전의 id (선택사항, 첫 리비전은 None)

        Returns:
            생성된 리비전
        """
        revision = Revision(
            id=str(uuid.uuid4()),
            document_id=document_id,
            source=source,
            author_id=author_id,
            summary=summary,
            parent_revision_id=parent_revision_id,
        )
        return self.repository.create(revision)

    def get(self, id: str) -> Optional[Revision]:
        """
        주어진 id로 리비전을 조회한다.

        id에 해당하는 리비전이 없으면 None을 반환한다.

        Args:
            id: 조회할 리비전의 고유 식별자

        Returns:
            조회된 리비전 또는 없으면 None
        """
        return self.repository.get(id)

    def list_by_document_id(self, document_id: str) -> list[Revision]:
        """
        주어진 문서의 리비전을 생성 순서대로 나열한다.

        Args:
            document_id: 조회할 문서의 고유 식별자

        Returns:
            문서의 리비전 목록 (생성 순서)
        """
        return self.repository.list_by_document_id(document_id)
