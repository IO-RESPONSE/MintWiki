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
    제목, 본문, 리다이렉트 대상, 카테고리에 질의어가 포함되는지(대소문자
    구분 없이) 확인해 검색 결과를 반환한다.
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
        제목, 본문, 리다이렉트 대상, 카테고리에 질의어가 포함된 문서를
        검색해 결과 목록으로 반환한다.

        Args:
            query: 검색 질의

        Returns:
            질의어가 제목, 본문, 리다이렉트 대상, 카테고리 중 하나에
            포함된 문서의 검색 결과 목록 (일치하는 문서가 없으면 빈 목록).
            query의 limit/offset에 따라 페이지네이션이 적용된다.
        """
        term = query.term.lower()
        matches = [
            SearchResult(document=document, score=1.0)
            for document in self._documents.values()
            if term in document.title.lower()
            or term in document.body.lower()
            or (document.redirect_target is not None and term in document.redirect_target.lower())
            or any(term in category.lower() for category in document.categories)
        ]
        paginated = matches[query.offset:]
        if query.limit is not None:
            paginated = paginated[: query.limit]
        return paginated

    async def delete(self, document_id: str) -> None:
        """
        주어진 id의 문서를 메모리 색인에서 삭제한다.

        색인에 존재하지 않는 id가 주어져도 오류 없이 무시한다.

        Args:
            document_id: 삭제할 검색 문서의 고유 식별자
        """
        self._documents.pop(document_id, None)
