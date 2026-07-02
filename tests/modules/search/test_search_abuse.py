"""검색(search) 모듈의 남용(abuse) 시나리오 회귀 테스트 자리 표시자(placeholder).

요청 빈도 제한, limit 상한, 문서 가시성(ACL) 연동 등 남용 방지 전체
스위트는 아직 만들어지지 않았다. 이 파일은 그보다 앞서, 현재 MVP 단계
(`SearchService`/`InMemorySearchAdapter`/`router.py`)가 실제로 허용하고
있는 남용 경로 몇 가지를 공격 시나리오 형태로 고정해 두어, 이후 태스크가
관련 코드를 건드릴 때 (의도한 강화인지 우연한 회귀인지) 조기에 구분할 수
있게 하기 위한 자리 표시자다.
"""
from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.search.document import SearchDocument
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.query import SearchQuery
from modules.search.router import router
from modules.search.service import SearchService


@pytest.fixture
def app() -> FastAPI:
    """검색 서비스가 준비된 테스트용 앱을 생성한다."""
    app = FastAPI()
    app.state.search_service = SearchService(InMemorySearchAdapter())
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """테스트용 클라이언트를 생성한다."""
    return TestClient(app)


class TestSearchRoutesHaveNoAuthenticationOrRateLimitWired:
    """검색 라우트에 인증/속도 제한이 전혀 연결되어 있지 않음을 확인한다."""

    def test_repeated_unauthenticated_searches_all_succeed(self, client: TestClient):
        # 로그인 헤더 없이도, 동일 질의를 짧은 시간 안에 여러 번 반복해도
        # 모두 200으로 성공해, 검색 엔드포인트를 통한 무제한 질의 도배가
        # 가능함을 고정한다.
        responses = [
            client.get("/title", params={"title": "Anything"}) for _ in range(50)
        ]

        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_indexing_endpoint_absence_does_not_stop_flooding_via_service(
        self, app: FastAPI
    ):
        # 색인 라우트가 아직 라우터에 연결되어 있지 않지만(README 참고),
        # SearchService.index_document()를 직접 호출하는 경로에도 호출
        # 빈도를 제한하는 장치가 없어, 같은 문서를 대량으로 반복 색인해도
        # 오류 없이 계속 성공함을 고정한다.
        for i in range(50):
            await app.state.search_service.index_document(
                SearchDocument(document_id="doc1", title=f"제목{i}")
            )

        results = await app.state.search_service.search(SearchQuery(term="제목49"))
        assert len(results) == 1


class TestSearchLimitHasNoUpperBound:
    """limit 쿼리 파라미터에 상한이 없어, 과도하게 큰 값도 그대로 받아들여짐을 확인한다."""

    @pytest.mark.asyncio
    async def test_extremely_large_limit_is_accepted_without_a_ceiling(
        self, app: FastAPI, client: TestClient
    ):
        for i in range(30):
            await app.state.search_service.index_document(
                SearchDocument(document_id=f"doc{i}", title=f"Apple {i}")
            )

        response = client.get(
            "/title", params={"title": "Apple", "limit": 1_000_000}
        )

        assert response.status_code == 200
        assert len(response.json()["results"]) == 30

    @pytest.mark.asyncio
    async def test_omitting_limit_returns_every_matching_document_unbounded(
        self, app: FastAPI, client: TestClient
    ):
        # limit을 아예 생략하면 서버가 임의로 상한을 적용하지 않고, 일치하는
        # 문서를 모두 한 번에 반환한다.
        for i in range(100):
            await app.state.search_service.index_document(
                SearchDocument(document_id=f"doc{i}", title=f"Apple {i}")
            )

        response = client.get("/title", params={"title": "Apple"})

        assert response.status_code == 200
        assert len(response.json()["results"]) == 100


class TestSearchTermHasNoMaximumLength:
    """검색 질의어 길이에 상한이 없어, 매우 긴 문자열도 그대로 처리됨을 확인한다."""

    def test_search_query_constructor_accepts_extremely_long_term(self):
        # SearchQuery는 term 길이에 아무런 상한을 두지 않으므로, 매우 긴
        # 문자열도 별다른 오류 없이 그대로 질의 객체로 받아들여진다.
        long_term = "가" * 100_000

        query = SearchQuery(term=long_term)

        assert query.term == long_term

    @pytest.mark.asyncio
    async def test_extremely_long_query_term_is_processed_by_the_adapter(
        self, app: FastAPI
    ):
        long_term = "가" * 100_000

        results = await app.state.search_service.search(SearchQuery(term=long_term))

        assert results == []


class TestSearchResultsAreNotFilteredByDocumentVisibility:
    """SearchDocument/InMemorySearchAdapter에 문서 가시성(ACL) 개념이 전혀 없음을 확인한다."""

    @pytest.mark.asyncio
    async def test_document_carries_no_visibility_or_owner_field(self):
        # SearchDocument 생성자는 비공개/소유자 관련 필드를 받지 않으므로,
        # 색인 단계에서부터 가시성 정보를 담을 방법이 없다.
        document = SearchDocument(document_id="doc1", title="비공개여야 할 문서")

        assert not hasattr(document, "visibility")
        assert not hasattr(document, "is_private")
        assert not hasattr(document, "owner_id")

    @pytest.mark.asyncio
    async def test_any_caller_can_search_a_document_with_sensitive_looking_content(
        self, app: FastAPI, client: TestClient
    ):
        # 문서 내용이 아무리 민감해 보여도, 검색 어댑터는 이를 구분하지
        # 않고 색인된 모든 문서를 동일하게 검색 대상으로 취급한다.
        await app.state.search_service.index_document(
            SearchDocument(
                document_id="secret-doc",
                title="내부 전용 문서",
                body="비공개 취급되어야 하는 민감한 본문",
            )
        )

        response = client.get("/body", params={"body": "민감한"})

        assert response.status_code == 200
        result_ids = {result["document_id"] for result in response.json()["results"]}
        assert result_ids == {"secret-doc"}


class TestSearchAdapterAcceptsArbitraryQueriesWithNoInputSanitization:
    """InMemorySearchAdapter가 질의어를 그대로 부분 일치 비교에만 사용함을 확인한다."""

    async def _matches(self, adapter: InMemorySearchAdapter, term: str) -> List[str]:
        results = await adapter.search(SearchQuery(term=term))
        return [result.document.document_id for result in results]

    @pytest.mark.asyncio
    async def test_query_term_containing_control_characters_is_processed_as_is(self):
        adapter = InMemorySearchAdapter()
        await adapter.index(
            SearchDocument(document_id="doc1", title="Title\x00WithNull")
        )

        matched = await self._matches(adapter, "\x00")

        assert matched == ["doc1"]
