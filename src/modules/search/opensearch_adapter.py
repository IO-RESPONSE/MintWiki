"""OpenSearch 검색 어댑터 골격."""
from typing import List, Optional

from modules.search.adapter import SearchAdapter
from modules.search.document import SearchDocument
from modules.search.query import SearchQuery
from modules.search.result import SearchResult


class OpenSearchSearchAdapter(SearchAdapter):
    """
    OpenSearch 연동을 위한 검색 어댑터 골격.

    SearchAdapter 인터페이스의 형태만 갖춘 골격으로, 실제 OpenSearch 서버와
    통신하는 클라이언트 연동은 아직 채워지지 않았다. 생성자는 이후 클라이언트를
    구성하는 데 필요한 접속 정보(host, index_name, api_key)만 보관하며,
    index()/search()/delete() 는 호출 시 NotImplementedError 를 발생시킨다.
    실제 OpenSearch 클라이언트 연동과 SearchAdapterConfig 를 통한 조립은
    이후 태스크에서 채워진다.
    """

    def __init__(self, host: str, index_name: str, api_key: Optional[str] = None):
        """
        OpenSearch 어댑터 골격을 초기화한다.

        Args:
            host: OpenSearch 서버 주소
            index_name: 색인할 OpenSearch 인덱스 이름
            api_key: OpenSearch API 키 (생략하면 None)
        """
        self.host = host
        self.index_name = index_name
        self.api_key = api_key

    async def index(self, document: SearchDocument) -> None:
        """
        검색 문서를 OpenSearch 색인에 추가하거나 갱신한다.

        아직 실제 OpenSearch 클라이언트 연동이 구현되지 않아 항상
        NotImplementedError 를 발생시킨다.

        Args:
            document: 색인할 검색 문서

        Raises:
            NotImplementedError: 항상 발생한다.
        """
        raise NotImplementedError("OpenSearch 어댑터는 아직 구현되지 않았습니다.")

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        주어진 질의로 OpenSearch 색인을 검색한다.

        아직 실제 OpenSearch 클라이언트 연동이 구현되지 않아 항상
        NotImplementedError 를 발생시킨다.

        Args:
            query: 검색 질의

        Raises:
            NotImplementedError: 항상 발생한다.
        """
        raise NotImplementedError("OpenSearch 어댑터는 아직 구현되지 않았습니다.")

    async def delete(self, document_id: str) -> None:
        """
        주어진 id의 문서를 OpenSearch 색인에서 삭제한다.

        아직 실제 OpenSearch 클라이언트 연동이 구현되지 않아 항상
        NotImplementedError 를 발생시킨다.

        Args:
            document_id: 삭제할 검색 문서의 고유 식별자

        Raises:
            NotImplementedError: 항상 발생한다.
        """
        raise NotImplementedError("OpenSearch 어댑터는 아직 구현되지 않았습니다.")

    async def health_check(self) -> bool:
        """
        OpenSearch 백엔드가 요청을 처리할 수 있는 상태인지 확인한다.

        아직 실제 OpenSearch 클라이언트 연동이 구현되지 않아 항상
        NotImplementedError 를 발생시킨다.

        Raises:
            NotImplementedError: 항상 발생한다.
        """
        raise NotImplementedError("OpenSearch 어댑터는 아직 구현되지 않았습니다.")
