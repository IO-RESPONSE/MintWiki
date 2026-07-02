"""검색 색인 잡 핸들러 테스트."""
import asyncio

from modules.jobs import (
    JobHandler,
    JobPayload,
    JobResult,
    SEARCH_INDEX_JOB_TYPE,
    SearchIndexJobHandler,
)
from modules.search import InMemorySearchAdapter, IndexDocumentJobPayload, SearchQuery


def _run(coro):
    """비동기 검색 어댑터 헬퍼를 동기 테스트 코드에서 실행하기 위한 유틸리티.

    handler.handle()이 내부에서 asyncio.run을 사용하므로, 테스트 자체를
    async로 만들면 이미 실행 중인 이벤트 루프와 충돌한다. 테스트는 동기로
    유지하고, 색인 상태를 검증할 때만 이 헬퍼로 이벤트 루프를 연다.
    """
    return asyncio.run(coro)


class TestSearchIndexJobHandlerJobType:
    """job_type 계약 테스트."""

    def test_exposes_search_index_job_type_constant(self):
        """job_type은 SEARCH_INDEX_JOB_TYPE 상수와 동일하다."""
        handler = SearchIndexJobHandler(InMemorySearchAdapter())

        assert handler.job_type == SEARCH_INDEX_JOB_TYPE
        assert handler.job_type == "search.index"

    def test_is_instance_of_job_handler(self):
        """SearchIndexJobHandler는 jobs 모듈의 공통 JobHandler를 상속한다."""
        handler = SearchIndexJobHandler(InMemorySearchAdapter())

        assert isinstance(handler, JobHandler)


class TestSearchIndexJobHandlerIndexing:
    """정상 페이로드를 색인하는 동작 테스트."""

    def test_handle_indexes_document_with_required_fields(self):
        """필수 필드만 있는 페이로드도 검색 어댑터에 색인된다."""
        adapter = InMemorySearchAdapter()
        handler = SearchIndexJobHandler(adapter)
        payload = IndexDocumentJobPayload(document_id="doc1", title="My Document")

        job_result = handler.handle(payload)

        assert isinstance(job_result, JobResult)
        assert job_result.success is True
        assert job_result.data == {"document_id": "doc1"}
        results = _run(adapter.search(SearchQuery(term="My Document")))
        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    def test_handle_indexes_document_with_all_fields(self):
        """모든 필드가 채워진 페이로드도 그대로 색인된다."""
        adapter = InMemorySearchAdapter()
        handler = SearchIndexJobHandler(adapter)
        payload = IndexDocumentJobPayload(
            document_id="doc2",
            title="Another Document",
            body="본문 내용입니다.",
            redirect_target="doc1",
            categories=["Wiki", "Technology"],
        )

        job_result = handler.handle(payload)

        assert job_result.success is True
        assert job_result.data == {"document_id": "doc2"}
        results = _run(adapter.search(SearchQuery(term="Technology")))
        assert len(results) == 1
        indexed = results[0].document
        assert indexed.document_id == "doc2"
        assert indexed.body == "본문 내용입니다."
        assert indexed.redirect_target == "doc1"
        assert indexed.categories == ["Wiki", "Technology"]

    def test_handle_reindexing_same_id_overwrites_previous_entry(self):
        """동일한 document_id로 다시 색인하면 이전 내용을 덮어쓴다."""
        adapter = InMemorySearchAdapter()
        handler = SearchIndexJobHandler(adapter)
        handler.handle(IndexDocumentJobPayload(document_id="doc1", title="Old Title"))

        handler.handle(IndexDocumentJobPayload(document_id="doc1", title="New Title"))

        results = _run(adapter.search(SearchQuery(term="New Title")))
        assert len(results) == 1
        assert results[0].document.title == "New Title"
        assert _run(adapter.search(SearchQuery(term="Old Title"))) == []


class TestSearchIndexJobHandlerInvalidPayload:
    """잘못된 페이로드 타입 처리 테스트."""

    def test_handle_rejects_non_index_document_payload(self):
        """IndexDocumentJobPayload가 아닌 페이로드는 실패 결과를 반환한다."""

        class OtherPayload(JobPayload):
            @property
            def job_type(self) -> str:
                return "other.job"

        handler = SearchIndexJobHandler(InMemorySearchAdapter())
        job_result = handler.handle(OtherPayload())

        assert job_result.success is False
        assert job_result.error is not None
