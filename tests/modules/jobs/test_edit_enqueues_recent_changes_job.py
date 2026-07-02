"""문서 편집 시 최근 변경 내역 작업을 큐에 적재하는 통합 테스트."""
import pytest

from modules.document.model import Document
from modules.document.repository import InMemoryDocumentRepository
from modules.document.service import DocumentService
from modules.jobs import JobPayload, QueueBackend, RecentChangesJobPayload
from modules.jobs.cache_purge_payload import CachePurgeJobPayload
from modules.jobs.edit_indexing_service import EditIndexingService
from modules.revision.model import Revision
from modules.revision.repository import InMemoryRevisionRepository
from modules.revision.service import RevisionService
from modules.search import IndexDocumentJobPayload
from tests.modules.jobs.test_queue_backend import ConcreteQueueBackend


class TestEditEnqueuesRecentChangesJob:
    """문서 편집 시 최근 변경 내역 작업이 큐에 적재되는지 확인."""

    @pytest.mark.asyncio
    async def test_create_revision_enqueues_recent_changes_job(self):
        """리비전을 생성하면 최근 변경 내역 작업을 큐에 적재한다."""
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

        # 색인 작업과 캐시 퍼지 작업과 최근 변경 내역 작업이 큐에 적재되었는지 확인
        index_job = await queue.dequeue()
        cache_purge_job = await queue.dequeue()
        recent_changes_job = await queue.dequeue()

        # 색인 작업 확인
        assert index_job is not None
        assert isinstance(index_job, IndexDocumentJobPayload)
        assert index_job.document_id == doc.id

        # 캐시 퍼지 작업 확인
        assert cache_purge_job is not None
        assert isinstance(cache_purge_job, CachePurgeJobPayload)
        assert cache_purge_job.source == "Updated content"

        # 최근 변경 내역 작업 확인
        assert recent_changes_job is not None
        assert isinstance(recent_changes_job, RecentChangesJobPayload)
        assert recent_changes_job.page_name == "Test Document"
        assert recent_changes_job.author_id == "author-1"
        assert recent_changes_job.summary == "First edit"

    @pytest.mark.asyncio
    async def test_recent_changes_job_contains_correct_fields(self):
        """편집 시 올바른 정보를 담은 최근 변경 내역 작업을 큐에 적재한다."""
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
            author_id="editor-1",
            summary="오타 수정",
            parent_revision_id=doc.current_revision_id,
        )

        # 색인 작업 확인 및 스킵
        index_job = await queue.dequeue()
        assert index_job is not None

        # 캐시 퍼지 작업 확인 및 스킵
        cache_purge_job = await queue.dequeue()
        assert cache_purge_job is not None

        # 최근 변경 내역 작업 확인
        recent_changes_job = await queue.dequeue()
        assert recent_changes_job is not None
        assert isinstance(recent_changes_job, RecentChangesJobPayload)
        assert recent_changes_job.page_name == "Wiki Page"
        assert recent_changes_job.author_id == "editor-1"
        assert recent_changes_job.summary == "오타 수정"
        assert recent_changes_job.occurred_at is not None

    @pytest.mark.asyncio
    async def test_multiple_edits_enqueue_multiple_recent_changes_jobs(self):
        """여러 번 편집하면 각각마다 최근 변경 내역 작업을 큐에 적재한다."""
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

        # 큐에서 순서대로 꺼내기: 색인작업1, 캐시퍼지1, 최근변경1, 색인작업2, 캐시퍼지2, 최근변경2
        job1 = await queue.dequeue()  # 색인 작업 1
        job2 = await queue.dequeue()  # 캐시 퍼지 작업 1
        job3 = await queue.dequeue()  # 최근 변경 내역 작업 1
        job4 = await queue.dequeue()  # 색인 작업 2
        job5 = await queue.dequeue()  # 캐시 퍼지 작업 2
        job6 = await queue.dequeue()  # 최근 변경 내역 작업 2
        job7 = await queue.dequeue()  # None (큐가 비어있음)

        # 첫 번째 편집의 작업들 확인
        assert job1 is not None
        assert isinstance(job1, IndexDocumentJobPayload)
        assert job1.body == "v2"

        assert job2 is not None
        assert isinstance(job2, CachePurgeJobPayload)
        assert job2.source == "v2"

        assert job3 is not None
        assert isinstance(job3, RecentChangesJobPayload)
        assert job3.page_name == "Document"
        assert job3.summary == "Edit 1"

        # 두 번째 편집의 작업들 확인
        assert job4 is not None
        assert isinstance(job4, IndexDocumentJobPayload)
        assert job4.body == "v3"

        assert job5 is not None
        assert isinstance(job5, CachePurgeJobPayload)
        assert job5.source == "v3"

        assert job6 is not None
        assert isinstance(job6, RecentChangesJobPayload)
        assert job6.page_name == "Document"
        assert job6.summary == "Edit 2"

        # 큐가 비어있음
        assert job7 is None


__all__ = ["TestEditEnqueuesRecentChangesJob"]
