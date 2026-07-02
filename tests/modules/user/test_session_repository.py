"""세션 저장소 인터페이스 테스트."""
import pytest

from modules.user.session_repository import SessionRepository


class TestSessionRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            SessionRepository()

    def test_create_method_exists(self):
        """저장소는 create 메서드를 정의한다."""
        assert hasattr(SessionRepository, "create")

    def test_get_method_exists(self):
        """저장소는 get 메서드를 정의한다."""
        assert hasattr(SessionRepository, "get")

    def test_delete_method_exists(self):
        """저장소는 delete 메서드를 정의한다."""
        assert hasattr(SessionRepository, "delete")
