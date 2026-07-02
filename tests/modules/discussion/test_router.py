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


class TestListThreads:
    """스레드 목록 조회 엔드포인트 테스트."""

    def test_list_threads_returns_threads_for_document(self, client: TestClient):
        """엔드포인트는 지정한 문서의 스레드 목록을 생성 순서대로 반환한다."""
        client.post(
            "/threads",
            json={"document_id": "doc1", "title": "첫 번째", "created_by": "user1"},
        )
        client.post(
            "/threads",
            json={"document_id": "doc1", "title": "두 번째", "created_by": "user1"},
        )
        client.post(
            "/threads",
            json={"document_id": "doc2", "title": "다른 문서", "created_by": "user1"},
        )

        response = client.get("/threads", params={"document_id": "doc1"})

        assert response.status_code == 200
        data = response.json()
        titles = [thread["title"] for thread in data["threads"]]
        assert titles == ["첫 번째", "두 번째"]

    def test_list_threads_with_no_threads_returns_empty_list(self, client: TestClient):
        """엔드포인트는 스레드가 없는 문서에 대해 빈 목록을 반환한다."""
        response = client.get("/threads", params={"document_id": "doc-without-threads"})

        assert response.status_code == 200
        assert response.json()["threads"] == []

    def test_list_threads_requires_document_id(self, client: TestClient):
        """엔드포인트는 document_id 없이 요청하면 422를 반환한다."""
        response = client.get("/threads")

        assert response.status_code == 422


class TestAddComment:
    """댓글 추가 엔드포인트 테스트."""

    def test_add_comment_with_valid_request(self, client: TestClient):
        """엔드포인트는 유효한 요청으로 댓글을 추가한다."""
        response = client.post(
            "/threads/thread1/comments",
            json={"body": "동의합니다.", "created_by": "user1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == "thread1"
        assert data["body"] == "동의합니다."
        assert data["created_by"] == "user1"
        assert data["is_hidden"] is False
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0

    def test_add_comment_generates_unique_ids(self, client: TestClient):
        """엔드포인트는 매 요청마다 고유한 id를 발급한다."""
        response1 = client.post(
            "/threads/thread1/comments",
            json={"body": "첫 번째", "created_by": "user1"},
        )
        response2 = client.post(
            "/threads/thread1/comments",
            json={"body": "두 번째", "created_by": "user1"},
        )

        assert response1.json()["id"] != response2.json()["id"]

    def test_add_comment_with_empty_body_returns_422(self, client: TestClient):
        """엔드포인트는 빈 본문으로 요청하면 422를 반환한다."""
        response = client.post(
            "/threads/thread1/comments",
            json={"body": "", "created_by": "user1"},
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_add_comment_with_empty_created_by_returns_422(self, client: TestClient):
        """엔드포인트는 빈 작성자 id로 요청하면 422를 반환한다."""
        response = client.post(
            "/threads/thread1/comments",
            json={"body": "본문", "created_by": ""},
        )

        assert response.status_code == 422


class TestListComments:
    """댓글 목록 조회 엔드포인트 테스트."""

    def test_list_comments_returns_comments_for_thread(self, client: TestClient):
        """엔드포인트는 지정한 스레드의 댓글 목록을 생성 순서대로 반환한다."""
        client.post(
            "/threads/thread1/comments",
            json={"body": "첫 번째", "created_by": "user1"},
        )
        client.post(
            "/threads/thread1/comments",
            json={"body": "두 번째", "created_by": "user1"},
        )
        client.post(
            "/threads/thread2/comments",
            json={"body": "다른 스레드", "created_by": "user1"},
        )

        response = client.get("/threads/thread1/comments")

        assert response.status_code == 200
        data = response.json()
        bodies = [comment["body"] for comment in data["comments"]]
        assert bodies == ["첫 번째", "두 번째"]

    def test_list_comments_with_no_comments_returns_empty_list(self, client: TestClient):
        """엔드포인트는 댓글이 없는 스레드에 대해 빈 목록을 반환한다."""
        response = client.get("/threads/thread-without-comments/comments")

        assert response.status_code == 200
        assert response.json()["comments"] == []
