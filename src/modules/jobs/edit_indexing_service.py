"""문서 편집 시 색인 작업을 큐에 적재하는 서비스."""
from typing import Optional

from modules.document.repository import DocumentRepository
from modules.jobs.cache_purge_payload import CachePurgeJobPayload
from modules.jobs.queue_backend import QueueBackend
from modules.revision.model import Revision
from modules.revision.service import RevisionService
from modules.search import IndexDocumentJobPayload


class EditIndexingService:
    """
    문서 편집 시 색인 작업을 조율하는 서비스.

    리비전 생성 시 자동으로 해당 문서의 색인 작업을 큐에 적재한다.
    """

    def __init__(
        self,
        revision_service: RevisionService,
        queue: QueueBackend,
        document_repository: Optional[DocumentRepository] = None,
    ):
        """
        서비스를 초기화한다.

        Args:
            revision_service: 리비전을 생성할 리비전 서비스
            queue: 색인 작업을 적재할 큐 백엔드
            document_repository: 문서 정보를 조회할 문서 저장소 (선택사항)
        """
        self._revision_service = revision_service
        self._queue = queue
        self._document_repository = document_repository

    async def create_revision_with_index_job(
        self,
        document_id: str,
        source: str,
        author_id: str,
        summary: str,
        parent_revision_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Revision:
        """
        새로운 리비전을 생성하고 색인 작업을 큐에 적재한다.

        리비전을 생성한 후, 해당 문서를 색인하기 위한 색인 작업 페이로드를
        큐에 적재한다.

        Args:
            document_id: 리비전이 속한 문서의 id
            source: 리비전의 소스 텍스트
            author_id: 저자의 id
            summary: 편집 요약
            parent_revision_id: 부모 리비전의 id (선택사항)
            title: 문서의 제목 (색인 작업에 필요함, 제공하지 않으면 저장소에서 조회)

        Returns:
            생성된 리비전
        """
        # 리비전 생성
        revision = await self._revision_service.create(
            document_id=document_id,
            source=source,
            author_id=author_id,
            summary=summary,
            parent_revision_id=parent_revision_id,
        )

        # 제목이 없으면 저장소에서 조회
        if title is None:
            if self._document_repository is None:
                raise ValueError("제목을 조회할 문서 저장소가 필요합니다")
            document = await self._document_repository.get(document_id)
            if document is None:
                raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
            title = document.title

        # 색인 작업 페이로드 생성
        index_payload = IndexDocumentJobPayload(
            document_id=document_id,
            title=title,
            body=source,
        )

        # 캐시 퍼지 작업 페이로드 생성
        cache_purge_payload = CachePurgeJobPayload(
            source=source,
            purge_all=False,
        )

        # 큐에 적재
        await self._queue.enqueue(index_payload)
        await self._queue.enqueue(cache_purge_payload)

        return revision


__all__ = ["EditIndexingService"]
