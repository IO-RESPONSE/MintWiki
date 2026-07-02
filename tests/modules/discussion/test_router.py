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
        assert isinstance(data["created_at"], str)
        assert data["closed_at"] is None
        assert data["paused_at"] is None

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

    def test_create_thread_with_whitespace_only_title_returns_422(self, client: TestClient):
        """엔드포인트는 공백만 있는 제목으로 요청하면 422를 반환한다."""
        response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "   ", "created_by": "user1"},
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_create_thread_normalizes_title_whitespace(self, client: TestClient):
        """엔드포인트는 제목의 주변 공백을 제거하고 내부 공백을 축소해서 반환한다."""
        response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "  제목에   대한  이견  ", "created_by": "user1"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "제목에 대한 이견"

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

    def test_list_threads_applies_limit_and_offset(self, client: TestClient):
        """엔드포인트는 limit과 offset 쿼리 파라미터로 스레드 목록을 제한한다."""
        for i in range(3):
            client.post(
                "/threads",
                json={"document_id": "doc1", "title": f"제목{i}", "created_by": "user1"},
            )

        response = client.get(
            "/threads", params={"document_id": "doc1", "limit": 1, "offset": 1}
        )

        assert response.status_code == 200
        titles = [thread["title"] for thread in response.json()["threads"]]
        assert titles == ["제목1"]

    def test_list_threads_applies_limit_only(self, client: TestClient):
        """엔드포인트는 offset 없이 limit만 지정해도 스레드 목록을 제한한다."""
        for i in range(3):
            client.post(
                "/threads",
                json={"document_id": "doc1", "title": f"제목{i}", "created_by": "user1"},
            )

        response = client.get("/threads", params={"document_id": "doc1", "limit": 2})

        assert response.status_code == 200
        titles = [thread["title"] for thread in response.json()["threads"]]
        assert titles == ["제목0", "제목1"]

    def test_list_threads_applies_offset_only(self, client: TestClient):
        """엔드포인트는 limit 없이 offset만 지정해도 그만큼 건너뛴 스레드 목록을 반환한다."""
        for i in range(3):
            client.post(
                "/threads",
                json={"document_id": "doc1", "title": f"제목{i}", "created_by": "user1"},
            )

        response = client.get("/threads", params={"document_id": "doc1", "offset": 1})

        assert response.status_code == 200
        titles = [thread["title"] for thread in response.json()["threads"]]
        assert titles == ["제목1", "제목2"]

    def test_list_threads_with_offset_beyond_total_returns_empty_list(self, client: TestClient):
        """엔드포인트는 offset이 전체 개수를 넘으면 빈 목록을 반환한다."""
        client.post(
            "/threads",
            json={"document_id": "doc1", "title": "제목", "created_by": "user1"},
        )

        response = client.get(
            "/threads", params={"document_id": "doc1", "offset": 10}
        )

        assert response.status_code == 200
        assert response.json()["threads"] == []

    def test_list_threads_with_invalid_limit_returns_422(self, client: TestClient):
        """엔드포인트는 0 이하의 limit으로 요청하면 422를 반환한다."""
        response = client.get(
            "/threads", params={"document_id": "doc1", "limit": 0}
        )

        assert response.status_code == 422

    def test_list_threads_with_negative_offset_returns_422(self, client: TestClient):
        """엔드포인트는 음수 offset으로 요청하면 422를 반환한다."""
        response = client.get(
            "/threads", params={"document_id": "doc1", "offset": -1}
        )

        assert response.status_code == 422


class TestCloseThread:
    """스레드 닫기 엔드포인트 테스트."""

    def test_close_thread_with_valid_id(self, client: TestClient):
        """엔드포인트는 열려 있는 스레드를 닫는다."""
        create_response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "제목", "created_by": "user1"},
        )
        thread_id = create_response.json()["id"]

        response = client.post(f"/threads/{thread_id}/close")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == thread_id
        assert data["status"] == "closed"
        assert data["closed_at"] is not None

    def test_close_nonexistent_thread_returns_404(self, client: TestClient):
        """엔드포인트는 존재하지 않는 스레드를 닫으려 하면 404를 반환한다."""
        response = client.post("/threads/nonexistent-id/close")

        assert response.status_code == 404
        assert "detail" in response.json()


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
        assert isinstance(data["created_at"], str)
        assert data["hidden_at"] is None

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

    def test_list_comments_applies_limit_and_offset(self, client: TestClient):
        """엔드포인트는 limit과 offset 쿼리 파라미터로 댓글 목록을 제한한다."""
        for i in range(3):
            client.post(
                "/threads/thread1/comments",
                json={"body": f"댓글{i}", "created_by": "user1"},
            )

        response = client.get(
            "/threads/thread1/comments", params={"limit": 1, "offset": 1}
        )

        assert response.status_code == 200
        bodies = [comment["body"] for comment in response.json()["comments"]]
        assert bodies == ["댓글1"]

    def test_list_comments_applies_limit_only(self, client: TestClient):
        """엔드포인트는 offset 없이 limit만 지정해도 댓글 목록을 제한한다."""
        for i in range(3):
            client.post(
                "/threads/thread1/comments",
                json={"body": f"댓글{i}", "created_by": "user1"},
            )

        response = client.get("/threads/thread1/comments", params={"limit": 2})

        assert response.status_code == 200
        bodies = [comment["body"] for comment in response.json()["comments"]]
        assert bodies == ["댓글0", "댓글1"]

    def test_list_comments_applies_offset_only(self, client: TestClient):
        """엔드포인트는 limit 없이 offset만 지정해도 그만큼 건너뛴 댓글 목록을 반환한다."""
        for i in range(3):
            client.post(
                "/threads/thread1/comments",
                json={"body": f"댓글{i}", "created_by": "user1"},
            )

        response = client.get("/threads/thread1/comments", params={"offset": 1})

        assert response.status_code == 200
        bodies = [comment["body"] for comment in response.json()["comments"]]
        assert bodies == ["댓글1", "댓글2"]

    def test_list_comments_with_offset_beyond_total_returns_empty_list(
        self, client: TestClient
    ):
        """엔드포인트는 offset이 전체 개수를 넘으면 빈 목록을 반환한다."""
        client.post(
            "/threads/thread1/comments",
            json={"body": "댓글", "created_by": "user1"},
        )

        response = client.get("/threads/thread1/comments", params={"offset": 10})

        assert response.status_code == 200
        assert response.json()["comments"] == []

    def test_list_comments_with_invalid_limit_returns_422(self, client: TestClient):
        """엔드포인트는 0 이하의 limit으로 요청하면 422를 반환한다."""
        response = client.get("/threads/thread1/comments", params={"limit": 0})

        assert response.status_code == 422

    def test_list_comments_with_negative_offset_returns_422(self, client: TestClient):
        """엔드포인트는 음수 offset으로 요청하면 422를 반환한다."""
        response = client.get("/threads/thread1/comments", params={"offset": -1})

        assert response.status_code == 422


class TestCloseThreadIdempotency:
    """스레드 닫기 엔드포인트의 반복 호출 동작 테스트."""

    def test_closing_already_closed_thread_stays_closed(self, client: TestClient):
        """이미 닫힌 스레드를 다시 닫아도 오류 없이 닫힌 상태를 유지한다."""
        create_response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "제목", "created_by": "user1"},
        )
        thread_id = create_response.json()["id"]
        client.post(f"/threads/{thread_id}/close")

        response = client.post(f"/threads/{thread_id}/close")

        assert response.status_code == 200
        assert response.json()["status"] == "closed"


class TestDiscussionApiIntegration:
    """여러 엔드포인트를 이어서 호출하는 통합 시나리오 테스트."""

    def test_thread_and_comment_flow_via_api(self, client: TestClient):
        """스레드 생성, 댓글 추가, 목록 조회, 닫기가 API를 통해 일관되게 반영된다."""
        create_response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "제목", "created_by": "user1"},
        )
        thread_id = create_response.json()["id"]

        client.post(
            f"/threads/{thread_id}/comments",
            json={"body": "첫 번째 댓글", "created_by": "user2"},
        )
        client.post(
            f"/threads/{thread_id}/comments",
            json={"body": "두 번째 댓글", "created_by": "user3"},
        )

        comments_response = client.get(f"/threads/{thread_id}/comments")
        bodies = [c["body"] for c in comments_response.json()["comments"]]
        assert bodies == ["첫 번째 댓글", "두 번째 댓글"]

        client.post(f"/threads/{thread_id}/close")

        threads_response = client.get("/threads", params={"document_id": "doc1"})
        threads = threads_response.json()["threads"]
        assert len(threads) == 1
        assert threads[0]["id"] == thread_id
        assert threads[0]["status"] == "closed"
