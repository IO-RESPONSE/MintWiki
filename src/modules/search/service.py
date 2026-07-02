"""검색 문서 색인과 질의를 담당하는 서비스."""
from typing import List

from modules.search.adapter import SearchAdapter
from modules.search.document import SearchDocument
from modules.search.errors import SearchServiceError
from modules.search.query import SearchQuery
from modules.search.result import SearchResult


class SearchService:
    """
    검색 문서 색인과 질의를 담당하는 서비스.

    실제 색인/검색 동작은 주입된 SearchAdapter에 위임한다. 원본 문서에서
    검색 문서를 구성하는 변환 로직이나 질의 결과의 정렬/페이지네이션 같은
    세부 동작은 이후 태스크에서 채워지므로, 이 서비스는 어댑터로의 위임만
    제공하는 골격이다.

    어댑터 호출 중 예외가 발생하면 SearchServiceError로 감싸 다시 던져,
    호출자가 구체적인 어댑터 구현과 무관하게 하나의 오류 타입만 처리하면
    되도록 한다.
    """

    def __init__(self, adapter: SearchAdapter):
        """
        서비스를 초기화한다.

        Args:
            adapter: 실제 색인/검색을 수행할 검색 어댑터
        """
        self.adapter = adapter

    async def index_document(self, document: SearchDocument) -> None:
        """
        검색 문서를 색인에 추가하거나 갱신한다.

        Args:
            document: 색인할 검색 문서

        Raises:
            SearchServiceError: 어댑터가 색인 중 예외를 던진 경우
        """
        try:
            await self.adapter.index(document)
        except Exception as error:
            raise SearchServiceError("index", error) from error

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        주어진 질의로 검색을 수행한다.

        Args:
            query: 검색 질의

        Returns:
            질의와 관련된 검색 결과 목록

        Raises:
            SearchServiceError: 어댑터가 검색 중 예외를 던진 경우
        """
        try:
            return await self.adapter.search(query)
        except Exception as error:
            raise SearchServiceError("search", error) from error

    async def delete_document(self, document_id: str) -> None:
        """
        주어진 id의 문서를 색인에서 삭제한다.

        Args:
            document_id: 삭제할 검색 문서의 고유 식별자

        Raises:
            SearchServiceError: 어댑터가 삭제 중 예외를 던진 경우
        """
        try:
            await self.adapter.delete(document_id)
        except Exception as error:
            raise SearchServiceError("delete", error) from error

    async def health_check(self) -> bool:
        """
        검색 백엔드가 요청을 처리할 수 있는 상태인지 확인한다.

        Returns:
            검색 백엔드가 정상이면 True, 그렇지 않으면 False

        Raises:
            SearchServiceError: 어댑터가 상태 확인 중 예외를 던진 경우
        """
        try:
            return await self.adapter.health_check()
        except Exception as error:
            raise SearchServiceError("health_check", error) from error
