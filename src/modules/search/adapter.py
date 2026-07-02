"""검색 어댑터 인터페이스."""
from abc import ABC, abstractmethod
from typing import List

from modules.search.document import SearchDocument
from modules.search.query import SearchQuery
from modules.search.result import SearchResult


class SearchAdapter(ABC):
    """
    검색 어댑터의 인터페이스.

    문서를 색인하고 질의를 받아 검색 결과를 반환하는 메서드를 정의한다.
    로컬 폴백 검색, 외부 검색 엔진 연동 등 구체적인 구현은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def index(self, document: SearchDocument) -> None:
        """
        검색 문서를 색인에 추가하거나 갱신한다.

        Args:
            document: 색인할 검색 문서
        """
        pass

    @abstractmethod
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        주어진 질의로 색인을 검색한다.

        Args:
            query: 검색 질의

        Returns:
            질의와 관련된 검색 결과 목록
        """
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> None:
        """
        주어진 id의 문서를 색인에서 삭제한다.

        Args:
            document_id: 삭제할 검색 문서의 고유 식별자
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        검색 백엔드가 요청을 처리할 수 있는 상태인지 확인한다.

        Returns:
            검색 백엔드가 정상이면 True, 그렇지 않으면 False
        """
        pass
