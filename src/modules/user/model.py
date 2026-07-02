"""사용자 도메인 모델."""
from typing import Optional


class EmptyUsernameError(Exception):
    """사용자명이 비어있을 때 발생."""

    pass


class User:
    """
    사용자를 나타내는 도메인 모델.

    사용자는 고유한 id, 사용자명, 그리고 선택적으로 표시 이름을 가진다.
    """

    def __init__(
        self,
        id: str,
        username: str,
        display_name: Optional[str] = None,
    ):
        """
        사용자를 생성한다.

        Args:
            id: 사용자의 고유 식별자
            username: 사용자의 로그인용 사용자명
            display_name: 화면에 표시할 이름 (선택사항, 기본값 None)

        Raises:
            EmptyUsernameError: 사용자명이 비어있거나 공백만 있는 경우
        """
        if not username or not username.strip():
            raise EmptyUsernameError("사용자명은 비어있을 수 없습니다")

        self.id = id
        self.username = username
        self.display_name = display_name
