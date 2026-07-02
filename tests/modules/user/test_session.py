"""세션 모델 테스트."""
from datetime import datetime, timedelta

import pytest
from modules.user.session import EmptySessionIdError, EmptyUserIdError, Session


class TestSessionConstruction:
    """세션 생성 테스트."""

    def test_creates_session_with_required_fields(self):
        """필수 필드로 세션을 생성한다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        expires_at = created_at + timedelta(hours=1)
        session = Session(
            id="session1",
            user_id="user1",
            created_at=created_at,
            expires_at=expires_at,
        )
        assert session.id == "session1"
        assert session.user_id == "user1"
        assert session.created_at == created_at
        assert session.expires_at == expires_at

    def test_rejects_empty_session_id(self):
        """빈 세션 id로 세션을 생성할 수 없다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        with pytest.raises(EmptySessionIdError):
            Session(
                id="",
                user_id="user1",
                created_at=created_at,
                expires_at=created_at + timedelta(hours=1),
            )

    def test_rejects_whitespace_only_session_id(self):
        """공백만 있는 세션 id로 세션을 생성할 수 없다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        with pytest.raises(EmptySessionIdError):
            Session(
                id="   ",
                user_id="user1",
                created_at=created_at,
                expires_at=created_at + timedelta(hours=1),
            )

    def test_rejects_empty_user_id(self):
        """빈 사용자 id로 세션을 생성할 수 없다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        with pytest.raises(EmptyUserIdError):
            Session(
                id="session1",
                user_id="",
                created_at=created_at,
                expires_at=created_at + timedelta(hours=1),
            )

    def test_rejects_whitespace_only_user_id(self):
        """공백만 있는 사용자 id로 세션을 생성할 수 없다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        with pytest.raises(EmptyUserIdError):
            Session(
                id="session1",
                user_id="   ",
                created_at=created_at,
                expires_at=created_at + timedelta(hours=1),
            )


class TestSessionExpiration:
    """세션 만료 확인 테스트."""

    def test_is_expired_returns_false_before_expiry(self):
        """만료 시각 이전에는 is_expired가 False를 반환한다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        expires_at = created_at + timedelta(hours=1)
        session = Session(
            id="session1",
            user_id="user1",
            created_at=created_at,
            expires_at=expires_at,
        )
        assert session.is_expired(created_at + timedelta(minutes=30)) is False

    def test_is_expired_returns_true_after_expiry(self):
        """만료 시각 이후에는 is_expired가 True를 반환한다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        expires_at = created_at + timedelta(hours=1)
        session = Session(
            id="session1",
            user_id="user1",
            created_at=created_at,
            expires_at=expires_at,
        )
        assert session.is_expired(expires_at + timedelta(seconds=1)) is True

    def test_is_expired_returns_true_at_exact_expiry_time(self):
        """만료 시각과 정확히 일치하면 is_expired가 True를 반환한다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        expires_at = created_at + timedelta(hours=1)
        session = Session(
            id="session1",
            user_id="user1",
            created_at=created_at,
            expires_at=expires_at,
        )
        assert session.is_expired(expires_at) is True
