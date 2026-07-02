"""토론 저장소 인터페이스 테스트."""
import pytest

from modules.discussion.repository import DiscussionRepository


class TestDiscussionRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            DiscussionRepository()

    def test_create_thread_method_exists(self):
        """저장소는 create_thread 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "create_thread")

    def test_get_thread_method_exists(self):
        """저장소는 get_thread 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "get_thread")

    def test_list_threads_by_document_id_method_exists(self):
        """저장소는 list_threads_by_document_id 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "list_threads_by_document_id")

    def test_update_thread_method_exists(self):
        """저장소는 update_thread 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "update_thread")

    def test_create_comment_method_exists(self):
        """저장소는 create_comment 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "create_comment")

    def test_list_comments_by_thread_id_method_exists(self):
        """저장소는 list_comments_by_thread_id 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "list_comments_by_thread_id")
