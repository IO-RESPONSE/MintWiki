"""사용자 저장소 인터페이스 테스트."""
import pytest

from modules.user.model import User
from modules.user.repository import (
    UserRepository,
    InMemoryUserRepository,
)


class TestUserRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            UserRepository()

    def test_create_method_exists(self):
        """저장소는 create 메서드를 정의한다."""
        assert hasattr(UserRepository, "create")

    def test_get_method_exists(self):
        """저장소는 get 메서드를 정의한다."""
        assert hasattr(UserRepository, "get")

    def test_get_by_username_method_exists(self):
        """저장소는 get_by_username 메서드를 정의한다."""
        assert hasattr(UserRepository, "get_by_username")


class TestInMemoryUserRepository:
    """인메모리 저장소 구현 테스트."""

    @pytest.mark.asyncio
    async def test_can_create_user(self):
        """인메모리 저장소는 사용자를 생성할 수 있다."""
        repo = InMemoryUserRepository()
        user = User(id="user1", username="alice", display_name="Alice")
        result = await repo.create(user)
        assert result.id == "user1"
        assert result.username == "alice"
        assert result.display_name == "Alice"

    @pytest.mark.asyncio
    async def test_can_fetch_user_by_id(self):
        """인메모리 저장소는 id로 사용자를 조회할 수 있다."""
        repo = InMemoryUserRepository()
        user = User(id="user1", username="alice")
        await repo.create(user)
        result = await repo.get("user1")
        assert result is not None
        assert result.id == "user1"
        assert result.username == "alice"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self):
        """인메모리 저장소는 없는 id를 조회하면 None을 반환한다."""
        repo = InMemoryUserRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_fetch_user_by_username(self):
        """인메모리 저장소는 사용자명으로 사용자를 조회할 수 있다."""
        repo = InMemoryUserRepository()
        user = User(id="user1", username="alice")
        await repo.create(user)
        result = await repo.get_by_username("alice")
        assert result is not None
        assert result.id == "user1"
        assert result.username == "alice"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_username(self):
        """인메모리 저장소는 없는 사용자명을 조회하면 None을 반환한다."""
        repo = InMemoryUserRepository()
        result = await repo.get_by_username("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_store_multiple_users(self):
        """인메모리 저장소는 여러 사용자를 저장할 수 있다."""
        repo = InMemoryUserRepository()
        alice = User(id="user1", username="alice")
        bob = User(id="user2", username="bob")
        await repo.create(alice)
        await repo.create(bob)

        result_alice = await repo.get_by_username("alice")
        result_bob = await repo.get_by_username("bob")
        assert result_alice.id == "user1"
        assert result_bob.id == "user2"
