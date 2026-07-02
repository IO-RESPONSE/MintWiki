"""문서 편집 시 색인 작업을 큐에 적재하는 통합 테스트."""
import pytest

from modules.document.model import Document
from modules.document.repository import InMemoryDocumentRepository
from modules.document.service import DocumentService
from modules.jobs import JobPayload, QueueBackend
from modules.jobs.edit_indexing_service import EditIndexingService
from modules.revision.model import Revision
from modules.revision.repository import InMemoryRevisionRepository
from modules.revision.service import RevisionService
from modules.search import IndexDocumentJobPayload
from tests.modules.jobs.test_queue_backend import ConcreteQueueBackend


class TestEditEnqueuesIndexJob:
    """문서 편집 시 색인 작업이 큐에 적재되는지 확인."""

    @pytest.mark.asyncio
    async def test_create_revision_enqueues_index_job(self):
        """리비전을 생성하면 색인 작업을 큐에 적재한다."""
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

        # 색인 작업이 큐에 적재되었는지 확인
        enqueued = await queue.dequeue()
        assert enqueued is not None
        assert isinstance(enqueued, IndexDocumentJobPayload)
        assert enqueued.document_id == doc.id
        assert enqueued.title == "Test Document"
        assert enqueued.body == "Updated content"

    @pytest.mark.asyncio
    async def test_edit_enqueues_index_job_with_correct_payload(self):
        """편집 시 정확한 문서 정보를 담은 색인 작업을 큐에 적재한다."""
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

        # 첫 번째 색인 작업 확인
        first_job = await queue.dequeue()
        assert first_job is not None
        assert first_job.title == "Wiki Page"
        assert first_job.body == "Content v2"

    @pytest.mark.asyncio
    async def test_multiple_edits_enqueue_multiple_jobs(self):
        """여러 번 편집하면 각각마다 색인 작업을 큐에 적재한다."""
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

        # 두 개의 색인 작업이 큐에 적재되었는지 확인
        job1 = await queue.dequeue()
        job2 = await queue.dequeue()
        job3 = await queue.dequeue()

        assert job1 is not None
        assert job1.body == "v2"
        assert job2 is not None
        assert job2.body == "v3"
        assert job3 is None  # 큐가 비어있음


__all__ = ["TestEditEnqueuesIndexJob"]
