"""사용자 차단 도메인 모델."""
from datetime import datetime
from typing import Optional


class EmptyBlockIdError(Exception):
    """차단 id가 비어있을 때 발생."""

    pass


class EmptyBlockUserIdError(Exception):
    """차단 대상 사용자 id가 비어있을 때 발생."""

    pass


class Block:
    """
    사용자 차단을 나타내는 도메인 모델.

    차단은 특정 사용자의 편집 등 행위를 제한하기 위해 생성되며,
    선택적으로 만료 시각을 가진다. 만료 시각이 없으면 무기한 차단을 의미한다.
    """

    def __init__(
        self,
        id: str,
        user_id: str,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        reason: Optional[str] = None,
        blocked_by: Optional[str] = None,
    ):
        """
        차단을 생성한다.

        Args:
            id: 차단의 고유 식별자
            user_id: 차단 대상 사용자의 id
            created_at: 차단이 생성된 시각
            expires_at: 차단이 만료되는 시각 (선택사항, None이면 무기한 차단)
            reason: 차단 사유 (선택사항)
            blocked_by: 차단을 수행한 관리자 사용자의 id (선택사항)

        Raises:
            EmptyBlockIdError: 차단 id가 비어있거나 공백만 있는 경우
            EmptyBlockUserIdError: 차단 대상 사용자 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyBlockIdError("차단 id는 비어있을 수 없습니다")
        if not user_id or not user_id.strip():
            raise EmptyBlockUserIdError("차단 대상 사용자 id는 비어있을 수 없습니다")

        self.id = id
        self.user_id = user_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.reason = reason
        self.blocked_by = blocked_by

    def is_active(self, now: datetime) -> bool:
        """주어진 시각 기준으로 차단이 유효한지 확인한다. 만료 시각이 없으면 항상 유효하다."""
        if self.expires_at is None:
            return True
        return now < self.expires_at
