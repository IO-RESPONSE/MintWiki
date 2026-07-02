"""차단 저장소 인터페이스 테스트."""
import pytest

from modules.user.block_repository import BlockRepository


class TestBlockRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            BlockRepository()

    def test_create_method_exists(self):
        """저장소는 create 메서드를 정의한다."""
        assert hasattr(BlockRepository, "create")

    def test_get_method_exists(self):
        """저장소는 get 메서드를 정의한다."""
        assert hasattr(BlockRepository, "get")

    def test_get_by_user_id_method_exists(self):
        """저장소는 get_by_user_id 메서드를 정의한다."""
        assert hasattr(BlockRepository, "get_by_user_id")

    def test_delete_method_exists(self):
        """저장소는 delete 메서드를 정의한다."""
        assert hasattr(BlockRepository, "delete")
