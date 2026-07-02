"""검색 라우터 테스트."""
from typing import List

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from modules.search.adapter import SearchAdapter
from modules.search.document import SearchDocument
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.query import SearchQuery
from modules.search.result import SearchResult
from modules.search.router import get_search_service, router
from modules.search.service import SearchService


class UnhealthySearchAdapter(SearchAdapter):
    """health_check가 항상 False를 반환하는 테스트 전용 어댑터."""

    async def index(self, document: SearchDocument) -> None:
        raise NotImplementedError

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        raise NotImplementedError

    async def delete(self, document_id: str) -> None:
        raise NotImplementedError

    async def health_check(self) -> bool:
        return False


class TestSearchRouterSkeleton:
    """router 객체가 APIRouter로 준비되어 있는지 확인한다."""

    def test_router_is_an_api_router(self):
        assert isinstance(router, APIRouter)


class TestSearchRouteRegistration:
    """search 라우터에 제목/본문 검색 라우트가 등록되어 있는지 확인한다."""

    def _registered_routes(self):
        return {
            (route.path, method)
            for route in router.routes
            for method in route.methods
        }

    def test_search_by_title_route_is_registered(self):
        assert ("/title", "GET") in self._registered_routes()

    def test_search_by_body_route_is_registered(self):
        assert ("/body", "GET") in self._registered_routes()

    def test_search_health_route_is_registered(self):
        assert ("/health", "GET") in self._registered_routes()

    def test_no_unexpected_routes_are_registered(self):
        """의도하지 않은 라우트가 실수로 추가되지 않았는지 확인한다."""
        assert self._registered_routes() == {
            ("/title", "GET"),
            ("/body", "GET"),
            ("/health", "GET"),
        }

    def test_routes_are_tagged_search(self):
        """모든 라우트가 OpenAPI 문서에서 search 태그로 묶이는지 확인한다."""
        for route in router.routes:
            assert route.tags == ["search"]


class TestGetSearchService:
    """get_search_service 의존성 함수 테스트."""

    @pytest.mark.asyncio
    async def test_returns_service_from_app_state(self):
        """의존성 함수는 request.app.state.search_service를 그대로 반환한다."""
        app = FastAPI()
        service = SearchService(InMemorySearchAdapter())
        app.state.search_service = service

        class DummyRequest:
            pass

        request = DummyRequest()
        request.app = app

        assert await get_search_service(request) is service


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


class TestSearchByBody:
    """본문 검색 엔드포인트 테스트."""

    @pytest.mark.asyncio
    async def test_search_by_body_returns_matching_document(
        self, app: FastAPI, client: TestClient
    ):
        """엔드포인트는 본문에 질의어가 포함된 문서를 반환한다."""
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc1", title="Doc One", body="Hello World")
        )

        response = client.get("/body", params={"body": "Hello"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["document_id"] == "doc1"
        assert data["results"][0]["title"] == "Doc One"
        assert data["results"][0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_search_by_body_returns_empty_list_when_no_match(
        self, app: FastAPI, client: TestClient
    ):
        """엔드포인트는 일치하는 문서가 없으면 빈 목록을 반환한다."""
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc1", title="Doc One", body="Hello World")
        )

        response = client.get("/body", params={"body": "Nonexistent"})

        assert response.status_code == 200
        assert response.json()["results"] == []

    @pytest.mark.asyncio
    async def test_search_by_body_returns_all_matching_documents(
        self, app: FastAPI, client: TestClient
    ):
        """엔드포인트는 질의어에 일치하는 여러 문서를 모두 반환한다."""
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc1", title="Doc One", body="Apple Pie")
        )
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc2", title="Doc Two", body="Apple Juice")
        )
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc3", title="Doc Three", body="Banana Bread")
        )

        response = client.get("/body", params={"body": "Apple"})

        assert response.status_code == 200
        result_ids = {result["document_id"] for result in response.json()["results"]}
        assert result_ids == {"doc1", "doc2"}

    def test_search_by_body_without_body_param_returns_422(self, client: TestClient):
        """엔드포인트는 body 쿼리 파라미터 없이 요청하면 422를 반환한다."""
        response = client.get("/body")

        assert response.status_code == 422

    def test_search_by_body_with_empty_body_returns_422(self, client: TestClient):
        """엔드포인트는 빈 질의어로 요청하면 422를 반환한다."""
        response = client.get("/body", params={"body": ""})

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_search_by_body_with_whitespace_only_body_returns_422(
        self, client: TestClient
    ):
        """엔드포인트는 공백만 있는 질의어로 요청하면 422를 반환한다."""
        response = client.get("/body", params={"body": "   "})

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_search_by_body_applies_limit_and_offset(
        self, app: FastAPI, client: TestClient
    ):
        """엔드포인트는 limit과 offset 쿼리 파라미터로 결과를 제한한다."""
        for i in range(3):
            await app.state.search_service.index_document(
                SearchDocument(
                    document_id=f"doc{i}", title=f"Doc {i}", body=f"Apple {i}"
                )
            )

        response = client.get(
            "/body", params={"body": "Apple", "limit": 1, "offset": 1}
        )

        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    def test_search_by_body_with_invalid_limit_returns_422(self, client: TestClient):
        """엔드포인트는 0 이하의 limit으로 요청하면 422를 반환한다."""
        response = client.get("/body", params={"body": "Apple", "limit": 0})

        assert response.status_code == 422

    def test_search_by_body_with_negative_offset_returns_422(self, client: TestClient):
        """엔드포인트는 음수 offset으로 요청하면 422를 반환한다."""
        response = client.get("/body", params={"body": "Apple", "offset": -1})

        assert response.status_code == 422


class TestSearchHealth:
    """검색 헬스 체크 엔드포인트 테스트."""

    def test_search_health_returns_healthy_true_when_adapter_is_healthy(
        self, client: TestClient
    ):
        """어댑터가 정상이면 healthy=True를 반환한다."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"healthy": True}

    def test_search_health_returns_healthy_false_when_adapter_is_unhealthy(self):
        """어댑터가 비정상이면 healthy=False를 반환한다."""
        app = FastAPI()
        app.state.search_service = SearchService(UnhealthySearchAdapter())
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"healthy": False}


class TestSearchResponseShape:
    """검색 응답이 계약된 필드만 노출하는지 확인한다."""

    @pytest.mark.asyncio
    async def test_search_by_title_response_exposes_only_declared_fields(
        self, app: FastAPI, client: TestClient
    ):
        """응답 항목은 document_id, title, score 외의 필드를 노출하지 않는다."""
        await app.state.search_service.index_document(
            SearchDocument(
                document_id="doc1",
                title="Hello World",
                body="비공개로 유지되어야 하는 본문",
                categories=["Category"],
            )
        )

        response = client.get("/title", params={"title": "Hello"})

        result = response.json()["results"][0]
        assert set(result.keys()) == {"document_id", "title", "score"}

    @pytest.mark.asyncio
    async def test_search_by_body_response_exposes_only_declared_fields(
        self, app: FastAPI, client: TestClient
    ):
        """응답 항목은 document_id, title, score 외의 필드를 노출하지 않는다."""
        await app.state.search_service.index_document(
            SearchDocument(
                document_id="doc1",
                title="Doc One",
                body="Hello World",
                categories=["Category"],
            )
        )

        response = client.get("/body", params={"body": "Hello"})

        result = response.json()["results"][0]
        assert set(result.keys()) == {"document_id", "title", "score"}


class TestSearchMatchesAcrossIndexedFields:
    """제목/본문 검색 엔드포인트가 리다이렉트 대상, 카테고리에도 매칭되는지 확인한다.

    두 엔드포인트 모두 동일한 SearchService/어댑터에 위임하므로, 질의어는
    title/body 파라미터 이름과 무관하게 색인된 모든 필드에 매칭된다.
    """

    @pytest.mark.asyncio
    async def test_search_by_title_matches_redirect_target(
        self, app: FastAPI, client: TestClient
    ):
        await app.state.search_service.index_document(
            SearchDocument(
                document_id="doc1", title="Doc One", redirect_target="TargetPage"
            )
        )

        response = client.get("/title", params={"title": "TargetPage"})

        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    @pytest.mark.asyncio
    async def test_search_by_title_matches_category(
        self, app: FastAPI, client: TestClient
    ):
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc1", title="Doc One", categories=["Science"])
        )

        response = client.get("/title", params={"title": "Science"})

        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    @pytest.mark.asyncio
    async def test_search_by_body_matches_redirect_target(
        self, app: FastAPI, client: TestClient
    ):
        await app.state.search_service.index_document(
            SearchDocument(
                document_id="doc1", title="Doc One", redirect_target="TargetPage"
            )
        )

        response = client.get("/body", params={"body": "TargetPage"})

        assert response.status_code == 200
        assert len(response.json()["results"]) == 1

    @pytest.mark.asyncio
    async def test_search_by_body_matches_category(
        self, app: FastAPI, client: TestClient
    ):
        await app.state.search_service.index_document(
            SearchDocument(document_id="doc1", title="Doc One", categories=["Science"])
        )

        response = client.get("/body", params={"body": "Science"})

        assert response.status_code == 200
        assert len(response.json()["results"]) == 1
