"""사용자 그룹 도메인 모델."""
from typing import List, Optional


class EmptyGroupNameError(Exception):
    """그룹명이 비어있을 때 발생."""

    pass


class Group:
    """
    사용자 그룹을 나타내는 도메인 모델.

    그룹은 고유한 id와 그룹명을 가지며, 소속 사용자 id 목록을 통해
    구성원을 관리한다. 그룹은 ACL 규칙에서 사용자를 묶어 권한을
    부여하는 단위로 사용된다.
    """

    def __init__(
        self,
        id: str,
        name: str,
        member_ids: Optional[List[str]] = None,
    ):
        """
        사용자 그룹을 생성한다.

        Args:
            id: 그룹의 고유 식별자
            name: 그룹의 이름
            member_ids: 그룹에 소속된 사용자 id 목록 (선택사항, 기본값 빈 목록)

        Raises:
            EmptyGroupNameError: 그룹명이 비어있거나 공백만 있는 경우
        """
        if not name or not name.strip():
            raise EmptyGroupNameError("그룹명은 비어있을 수 없습니다")

        self.id = id
        self.name = name
        self.member_ids = list(member_ids) if member_ids else []

    def has_member(self, user_id: str) -> bool:
        """주어진 사용자 id가 그룹에 소속되어 있는지 확인한다."""
        return user_id in self.member_ids

    def add_member(self, user_id: str) -> None:
        """사용자를 그룹에 추가한다. 이미 소속된 경우 중복 추가하지 않는다."""
        if user_id not in self.member_ids:
            self.member_ids.append(user_id)

    def remove_member(self, user_id: str) -> None:
        """사용자를 그룹에서 제외한다. 소속되어 있지 않으면 아무 동작도 하지 않는다."""
        if user_id in self.member_ids:
            self.member_ids.remove(user_id)
