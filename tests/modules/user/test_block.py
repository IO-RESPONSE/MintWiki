"""차단 모델 테스트."""
from datetime import datetime, timedelta

import pytest
from modules.user.block import Block, EmptyBlockIdError, EmptyBlockUserIdError


class TestBlockConstruction:
    """차단 생성 테스트."""

    def test_creates_block_with_required_fields(self):
        """필수 필드로 차단을 생성한다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        block = Block(
            id="block1",
            user_id="user1",
            created_at=created_at,
        )
        assert block.id == "block1"
        assert block.user_id == "user1"
        assert block.created_at == created_at
        assert block.expires_at is None
        assert block.reason is None
        assert block.blocked_by is None

    def test_creates_block_with_optional_fields(self):
        """선택 필드를 포함하여 차단을 생성한다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        expires_at = created_at + timedelta(days=7)
        block = Block(
            id="block1",
            user_id="user1",
            created_at=created_at,
            expires_at=expires_at,
            reason="반복적인 문서 훼손",
            blocked_by="admin1",
        )
        assert block.expires_at == expires_at
        assert block.reason == "반복적인 문서 훼손"
        assert block.blocked_by == "admin1"

    def test_rejects_empty_block_id(self):
        """빈 차단 id로 차단을 생성할 수 없다."""
        with pytest.raises(EmptyBlockIdError):
            Block(id="", user_id="user1", created_at=datetime(2026, 1, 1))

    def test_rejects_whitespace_only_block_id(self):
        """공백만 있는 차단 id로 차단을 생성할 수 없다."""
        with pytest.raises(EmptyBlockIdError):
            Block(id="   ", user_id="user1", created_at=datetime(2026, 1, 1))

    def test_rejects_empty_user_id(self):
        """빈 사용자 id로 차단을 생성할 수 없다."""
        with pytest.raises(EmptyBlockUserIdError):
            Block(id="block1", user_id="", created_at=datetime(2026, 1, 1))

    def test_rejects_whitespace_only_user_id(self):
        """공백만 있는 사용자 id로 차단을 생성할 수 없다."""
        with pytest.raises(EmptyBlockUserIdError):
            Block(id="block1", user_id="   ", created_at=datetime(2026, 1, 1))


class TestBlockActiveState:
    """차단 유효 상태 확인 테스트."""

    def test_is_active_true_when_no_expiry(self):
        """만료 시각이 없으면 항상 유효하다."""
        block = Block(
            id="block1",
            user_id="user1",
            created_at=datetime(2026, 1, 1),
        )
        assert block.is_active(datetime(2099, 1, 1)) is True

    def test_is_active_true_before_expiry(self):
        """만료 시각 이전에는 유효하다."""
        created_at = datetime(2026, 1, 1)
        expires_at = created_at + timedelta(days=1)
        block = Block(
            id="block1",
            user_id="user1",
            created_at=created_at,
            expires_at=expires_at,
        )
        assert block.is_active(created_at + timedelta(hours=12)) is True

    def test_is_active_false_after_expiry(self):
        """만료 시각 이후에는 유효하지 않다."""
        created_at = datetime(2026, 1, 1)
        expires_at = created_at + timedelta(days=1)
        block = Block(
            id="block1",
            user_id="user1",
            created_at=created_at,
            expires_at=expires_at,
        )
        assert block.is_active(expires_at + timedelta(seconds=1)) is False

    def test_is_active_false_at_exact_expiry_time(self):
        """만료 시각과 정확히 일치하면 유효하지 않다."""
        created_at = datetime(2026, 1, 1)
        expires_at = created_at + timedelta(days=1)
        block = Block(
            id="block1",
            user_id="user1",
            created_at=created_at,
            expires_at=expires_at,
        )
        assert block.is_active(expires_at) is False
