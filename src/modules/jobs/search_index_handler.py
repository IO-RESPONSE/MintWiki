"""검색 색인 잡 핸들러."""
import asyncio

from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
from modules.jobs.result import JobResult
from modules.search.adapter import SearchAdapter
from modules.search.job_payload import IndexDocumentJobPayload

SEARCH_INDEX_JOB_TYPE = "search.index"


class SearchIndexJobHandler(JobHandler):
    """
    IndexDocumentJobPayload를 받아 검색 어댑터에 문서를 색인하는 핸들러.

    handle()은 JobHandler 계약상 동기 메서드이므로, 검색 어댑터의 비동기
    index() 호출은 asyncio.run으로 감싸 실행한다.
    """

    def __init__(self, adapter: SearchAdapter):
        """
        핸들러를 생성한다.

        Args:
            adapter: 색인을 수행할 검색 어댑터
        """
        self._adapter = adapter

    @property
    def job_type(self) -> str:
        return SEARCH_INDEX_JOB_TYPE

    def handle(self, payload: JobPayload) -> JobResult:
        """
        문서 색인 페이로드를 실행해 검색 어댑터에 문서를 반영한다.

        Args:
            payload: 실행할 IndexDocumentJobPayload

        Returns:
            색인 성공 시 문서 id를 담은 JobResult, 페이로드 타입이 맞지
            않으면 실패 JobResult
        """
        if not isinstance(payload, IndexDocumentJobPayload):
            return JobResult.fail(
                "SearchIndexJobHandler는 IndexDocumentJobPayload만 처리할 수 있습니다: "
                f"{type(payload).__name__}"
            )

        document = payload.to_search_document()
        asyncio.run(self._adapter.index(document))
        return JobResult.ok(data={"document_id": document.document_id})


__all__ = ["SEARCH_INDEX_JOB_TYPE", "SearchIndexJobHandler"]
