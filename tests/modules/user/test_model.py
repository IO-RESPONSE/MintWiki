"""사용자 모델 테스트."""
import pytest
from modules.user.model import EmptyUsernameError, User


class TestUserConstruction:
    """사용자 생성 테스트."""

    def test_creates_user_with_required_fields(self):
        """필수 필드로 사용자를 생성한다."""
        user = User(id="user1", username="alice")
        assert user.id == "user1"
        assert user.username == "alice"
        assert user.display_name is None

    def test_creates_user_with_display_name(self):
        """표시 이름을 포함하여 사용자를 생성한다."""
        user = User(id="user2", username="bob", display_name="Bob Smith")
        assert user.id == "user2"
        assert user.username == "bob"
        assert user.display_name == "Bob Smith"

    def test_preserves_unicode_username(self):
        """유니코드 사용자명을 그대로 보존한다."""
        user = User(id="user3", username="한글사용자")
        assert user.username == "한글사용자"

    def test_rejects_empty_username(self):
        """빈 사용자명으로 사용자를 생성할 수 없다."""
        with pytest.raises(EmptyUsernameError):
            User(id="user4", username="")

    def test_rejects_whitespace_only_username(self):
        """공백만 있는 사용자명으로 사용자를 생성할 수 없다."""
        with pytest.raises(EmptyUsernameError):
            User(id="user5", username="   ")
