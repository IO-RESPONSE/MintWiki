"""문서 편집 시 캐시 퍼지 작업을 큐에 적재하는 통합 테스트."""
import pytest

from modules.document.model import Document
from modules.document.repository import InMemoryDocumentRepository
from modules.document.service import DocumentService
from modules.jobs import JobPayload, QueueBackend
from modules.jobs.cache_purge_payload import CachePurgeJobPayload
from modules.jobs.edit_indexing_service import EditIndexingService
from modules.revision.model import Revision
from modules.revision.repository import InMemoryRevisionRepository
from modules.revision.service import RevisionService
from modules.search import IndexDocumentJobPayload
from tests.modules.jobs.test_queue_backend import ConcreteQueueBackend


class TestEditEnqueuesCachePurgeJob:
    """문서 편집 시 캐시 퍼지 작업이 큐에 적재되는지 확인."""

    @pytest.mark.asyncio
    async def test_create_revision_enqueues_cache_purge_job(self):
        """리비전을 생성하면 캐시 퍼지 작업을 큐에 적재한다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        queue = ConcreteQueueBackend()

        doc_service = DocumentService(doc_repo, rev_repo)
        rev_service = RevisionService(rev_repo)
        edit_service = EditIndexingService(rev_service, queue, doc_repo)

        # 문서 생성
        doc = await doc_service.create("Test Document", source="Initial content")

        # 문서 편집 (새 리비전 생성)
        revision = await edit_service.create_revision_with_index_job(
            document_id=doc.id,
            source="Updated content",
            author_id="author-1",
            summary="First edit",
            parent_revision_id=doc.current_revision_id,
        )

        # 색인 작업과 캐시 퍼지 작업이 큐에 적재되었는지 확인
        index_job = await queue.dequeue()
        cache_purge_job = await queue.dequeue()

        # 색인 작업 확인
        assert index_job is not None
        assert isinstance(index_job, IndexDocumentJobPayload)
        assert index_job.document_id == doc.id

        # 캐시 퍼지 작업 확인
        assert cache_purge_job is not None
        assert isinstance(cache_purge_job, CachePurgeJobPayload)
        assert cache_purge_job.source == "Updated content"
        assert cache_purge_job.purge_all is False

    @pytest.mark.asyncio
    async def test_cache_purge_job_contains_updated_source(self):
        """편집 시 업데이트된 소스가 캐시 퍼지 작업에 포함된다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        queue = ConcreteQueueBackend()

        doc_service = DocumentService(doc_repo, rev_repo)
        rev_service = RevisionService(rev_repo)
        edit_service = EditIndexingService(rev_service, queue, doc_repo)

        # 문서 생성
        doc = await doc_service.create("Wiki Page", source="Content v1")

        # 첫 번째 편집
        await edit_service.create_revision_with_index_job(
            document_id=doc.id,
            source="Content v2",
            author_id="author-1",
            summary="Update",
            parent_revision_id=doc.current_revision_id,
        )

        # 색인 작업 확인 및 스킵
        index_job = await queue.dequeue()
        assert index_job is not None

        # 캐시 퍼지 작업 확인
        cache_purge_job = await queue.dequeue()
        assert cache_purge_job is not None
        assert isinstance(cache_purge_job, CachePurgeJobPayload)
        assert cache_purge_job.source == "Content v2"

    @pytest.mark.asyncio
    async def test_multiple_edits_enqueue_multiple_cache_purge_jobs(self):
        """여러 번 편집하면 각각마다 캐시 퍼지 작업을 큐에 적재한다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        queue = ConcreteQueueBackend()

        doc_service = DocumentService(doc_repo, rev_repo)
        rev_service = RevisionService(rev_repo)
        edit_service = EditIndexingService(rev_service, queue, doc_repo)

        # 문서 생성
        doc = await doc_service.create("Document", source="v1")

        # 첫 번째 편집
        rev1 = await edit_service.create_revision_with_index_job(
            document_id=doc.id,
            source="v2",
            author_id="author-1",
            summary="Edit 1",
            parent_revision_id=doc.current_revision_id,
        )

        # 두 번째 편집
        rev2 = await edit_service.create_revision_with_index_job(
            document_id=doc.id,
            source="v3",
            author_id="author-1",
            summary="Edit 2",
            parent_revision_id=rev1.id,
        )

        # 큐에서 순서대로 꺼내기: 색인작업1, 캐시퍼지1, 색인작업2, 캐시퍼지2
        job1 = await queue.dequeue()  # 색인 작업 1
        job2 = await queue.dequeue()  # 캐시 퍼지 작업 1
        job3 = await queue.dequeue()  # 색인 작업 2
        job4 = await queue.dequeue()  # 캐시 퍼지 작업 2
        job5 = await queue.dequeue()  # None (큐가 비어있음)

        # 첫 번째 편집의 작업들 확인
        assert job1 is not None
        assert isinstance(job1, IndexDocumentJobPayload)
        assert job1.body == "v2"

        assert job2 is not None
        assert isinstance(job2, CachePurgeJobPayload)
        assert job2.source == "v2"

        # 두 번째 편집의 작업들 확인
        assert job3 is not None
        assert isinstance(job3, IndexDocumentJobPayload)
        assert job3.body == "v3"

        assert job4 is not None
        assert isinstance(job4, CachePurgeJobPayload)
        assert job4.source == "v3"

        # 큐가 비어있음
        assert job5 is None


__all__ = ["TestEditEnqueuesCachePurgeJob"]
