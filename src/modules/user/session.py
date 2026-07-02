"""세션 도메인 모델."""
from datetime import datetime


class EmptySessionIdError(Exception):
    """세션 id가 비어있을 때 발생."""

    pass


class EmptyUserIdError(Exception):
    """사용자 id가 비어있을 때 발생."""

    pass


class Session:
    """
    로그인한 사용자의 세션을 나타내는 도메인 모델.

    세션은 고유한 id로 사용자를 식별하며, 생성 시각과 만료 시각을 통해
    유효 기간을 관리한다.
    """

    def __init__(
        self,
        id: str,
        user_id: str,
        created_at: datetime,
        expires_at: datetime,
    ):
        """
        세션을 생성한다.

        Args:
            id: 세션의 고유 식별자
            user_id: 세션이 속한 사용자의 id
            created_at: 세션이 생성된 시각
            expires_at: 세션이 만료되는 시각

        Raises:
            EmptySessionIdError: 세션 id가 비어있거나 공백만 있는 경우
            EmptyUserIdError: 사용자 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptySessionIdError("세션 id는 비어있을 수 없습니다")
        if not user_id or not user_id.strip():
            raise EmptyUserIdError("사용자 id는 비어있을 수 없습니다")

        self.id = id
        self.user_id = user_id
        self.created_at = created_at
        self.expires_at = expires_at

    def is_expired(self, now: datetime) -> bool:
        """주어진 시각 기준으로 세션이 만료되었는지 확인한다."""
        return now >= self.expires_at
