"""토론 라우터 테스트."""
import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from modules.discussion.repository import InMemoryDiscussionRepository
from modules.discussion.router import router
from modules.discussion.service import DiscussionService


class TestDiscussionRouterSkeleton:
    """router 객체가 APIRouter로 준비되어 있는지 확인한다."""

    def test_router_is_an_api_router(self):
        assert isinstance(router, APIRouter)


@pytest.fixture
def client() -> TestClient:
    """토론 서비스가 준비된 테스트용 앱과 클라이언트를 생성한다.

    discussion 라우터는 아직 main.py에 등록되지 않았으므로(이후 태스크),
    이 테스트에서 별도의 앱을 구성해 라우터를 마운트한다.
    """
    app = FastAPI()
    app.state.discussion_service = DiscussionService(InMemoryDiscussionRepository())
    app.include_router(router)
    return TestClient(app)


class TestCreateThread:
    """스레드 생성 엔드포인트 테스트."""

    def test_create_thread_with_valid_request(self, client: TestClient):
        """엔드포인트는 유효한 요청으로 스레드를 생성한다."""
        response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "제목", "created_by": "user1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc1"
        assert data["title"] == "제목"
        assert data["created_by"] == "user1"
        assert data["status"] == "open"
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0

    def test_create_thread_generates_unique_ids(self, client: TestClient):
        """엔드포인트는 매 요청마다 고유한 id를 발급한다."""
        response1 = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "첫 번째", "created_by": "user1"},
        )
        response2 = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "두 번째", "created_by": "user1"},
        )

        assert response1.json()["id"] != response2.json()["id"]

    def test_create_thread_with_empty_title_returns_422(self, client: TestClient):
        """엔드포인트는 빈 제목으로 요청하면 422를 반환한다."""
        response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "", "created_by": "user1"},
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_create_thread_with_empty_document_id_returns_422(self, client: TestClient):
        """엔드포인트는 빈 문서 id로 요청하면 422를 반환한다."""
        response = client.post(
            "/threads",
            json={"document_id": "", "title": "제목", "created_by": "user1"},
        )

        assert response.status_code == 422

    def test_create_thread_with_empty_created_by_returns_422(self, client: TestClient):
        """엔드포인트는 빈 작성자 id로 요청하면 422를 반환한다."""
        response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "제목", "created_by": ""},
        )

        assert response.status_code == 422
