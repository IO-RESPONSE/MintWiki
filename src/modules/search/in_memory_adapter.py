"""메모리 기반 검색 어댑터 구현."""
from typing import Dict, List

from modules.search.adapter import SearchAdapter
from modules.search.document import SearchDocument
from modules.search.query import SearchQuery
from modules.search.result import SearchResult


class InMemorySearchAdapter(SearchAdapter):
    """
    메모리에 검색 문서를 색인하는 로컬 폴백 검색 어댑터.

    외부 검색 엔진 없이 개발/테스트 단계에서 사용하기 위한 구현으로,
    제목에 질의어가 포함되는지(대소문자 구분 없이) 확인해 검색 결과를
    반환한다. 본문 검색, 리다이렉트 검색 등 추가 색인 필드를 활용한
    검색은 후속 태스크에서 다룬다.
    """

    def __init__(self):
        """검색 어댑터를 초기화한다."""
        self._documents: Dict[str, SearchDocument] = {}

    async def index(self, document: SearchDocument) -> None:
        """
        검색 문서를 메모리 색인에 추가하거나 갱신한다.

        Args:
            document: 색인할 검색 문서
        """
        self._documents[document.document_id] = document

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        제목에 질의어가 포함된 문서를 검색해 결과 목록으로 반환한다.

        Args:
            query: 검색 질의

        Returns:
            질의어가 제목에 포함된 문서의 검색 결과 목록 (일치하는 문서가 없으면 빈 목록)
        """
        term = query.term.lower()
        return [
            SearchResult(document=document, score=1.0)
            for document in self._documents.values()
            if term in document.title.lower()
        ]
