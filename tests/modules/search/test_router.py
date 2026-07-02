"""검색 라우터 테스트."""
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from modules.search.document import SearchDocument
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.router import router
from modules.search.service import SearchService


class TestSearchRouterSkeleton:
    """router 객체가 APIRouter로 준비되어 있는지 확인한다."""

    def test_router_is_an_api_router(self):
        assert isinstance(router, APIRouter)


class TestSearchRouteRegistration:
    """search 라우터에 제목 검색 라우트가 등록되어 있는지 확인한다."""

    def _registered_routes(self):
        return {
            (route.path, method)
            for route in router.routes
            for method in route.methods
        }

    def test_search_by_title_route_is_registered(self):
        assert ("/title", "GET") in self._registered_routes()

    def test_no_unexpected_routes_are_registered(self):
        """의도하지 않은 라우트가 실수로 추가되지 않았는지 확인한다."""
        assert self._registered_routes() == {("/title", "GET")}


@pytest.fixture
def app() -> FastAPI:
    """검색 서비스가 준비된 테스트용 앱을 생성한다.

    search 라우터는 아직 main.py에 등록되지 않았으므로(이후 태스크),
    이 테스트에서 별도의 앱을 구성해 라우터를 마운트한다.
    """
    app = FastAPI()
    app.state.search_service = SearchService(InMemorySearchAdapter())
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """테스트용 클라이언트를 생성한다."""
    return TestClient(app)


class TestSearchByTitle:
    """제목 검색 엔드포인트 테스트."""

    @pytest.mark.asyncio
    async def test_search_by_title_returns_matching_document(
        self, app: FastAPI, client: TestClient
    ):
        """엔드포인트는 제목에 질의어가 포함된 문서를 반환한다."""
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc1", title="Hello World")
        )

        response = client.get("/title", params={"title": "Hello"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["document_id"] == "doc1"
        assert data["results"][0]["title"] == "Hello World"
        assert data["results"][0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_search_by_title_returns_empty_list_when_no_match(
        self, app: FastAPI, client: TestClient
    ):
        """엔드포인트는 일치하는 문서가 없으면 빈 목록을 반환한다."""
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc1", title="Hello World")
        )

        response = client.get("/title", params={"title": "Nonexistent"})

        assert response.status_code == 200
        assert response.json()["results"] == []

    @pytest.mark.asyncio
    async def test_search_by_title_returns_all_matching_documents(
        self, app: FastAPI, client: TestClient
    ):
        """엔드포인트는 질의어에 일치하는 여러 문서를 모두 반환한다."""
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc1", title="Apple Pie")
        )
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc2", title="Apple Juice")
        )
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc3", title="Banana Bread")
        )

        response = client.get("/title", params={"title": "Apple"})

        assert response.status_code == 200
        result_ids = {result["document_id"] for result in response.json()["results"]}
        assert result_ids == {"doc1", "doc2"}

    def test_search_by_title_without_title_param_returns_422(self, client: TestClient):
        """엔드포인트는 title 쿼리 파라미터 없이 요청하면 422를 반환한다."""
        response = client.get("/title")

        assert response.status_code == 422

    def test_search_by_title_with_empty_title_returns_422(self, client: TestClient):
        """엔드포인트는 빈 질의어로 요청하면 422를 반환한다."""
        response = client.get("/title", params={"title": ""})

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_search_by_title_with_whitespace_only_title_returns_422(
        self, client: TestClient
    ):
        """엔드포인트는 공백만 있는 질의어로 요청하면 422를 반환한다."""
        response = client.get("/title", params={"title": "   "})

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_search_by_title_applies_limit_and_offset(
        self, app: FastAPI, client: TestClient
    ):
        """엔드포인트는 limit과 offset 쿼리 파라미터로 결과를 제한한다."""
        for i in range(3):
            await app.state.search_service.index_document(
                SearchDocument(document_id=f"doc{i}", title=f"Apple {i}")
            )

        response = client.get(
            "/title", params={"title": "Apple", "limit": 1, "offset": 1}
        )

        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    def test_search_by_title_with_invalid_limit_returns_422(self, client: TestClient):
        """엔드포인트는 0 이하의 limit으로 요청하면 422를 반환한다."""
        response = client.get("/title", params={"title": "Apple", "limit": 0})

        assert response.status_code == 422

    def test_search_by_title_with_negative_offset_returns_422(self, client: TestClient):
        """엔드포인트는 음수 offset으로 요청하면 422를 반환한다."""
        response = client.get("/title", params={"title": "Apple", "offset": -1})

        assert response.status_code == 422
