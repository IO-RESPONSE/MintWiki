"""검색 색인 재구축(reindex) 명령 골격."""
from typing import Iterable

from modules.search.document import SearchDocument
from modules.search.service import SearchService


class SearchReindexCommand:
    """
    검색 색인을 처음부터 다시 구축하는 명령의 골격.

    document_source가 제공하는 문서를 순서대로 SearchService.index_document에
    위임해 색인을 재구축한다. document_source가 실제 위키 문서 저장소(document
    모듈)에서 문서 목록을 가져오도록 연동하는 것은 이후 태스크에서 채워지며,
    지금은 호출자가 넘겨주는 반복 가능 객체를 그대로 순회하는 골격만 제공한다.
    """

    def __init__(self, service: SearchService, document_source: Iterable[SearchDocument]):
        """
        재색인 명령을 초기화한다.

        Args:
            service: 문서 색인을 위임할 검색 서비스
            document_source: 재색인 대상 문서를 순서대로 제공하는 반복 가능 객체
        """
        self.service = service
        self.document_source = document_source

    async def run(self) -> int:
        """
        document_source가 제공하는 모든 문서를 색인에 다시 추가한다.

        Returns:
            색인을 완료한 문서 개수

        Raises:
            SearchServiceError: 어댑터가 색인 중 예외를 던진 경우
        """
        count = 0
        for document in self.document_source:
            await self.service.index_document(document)
            count += 1
        return count
