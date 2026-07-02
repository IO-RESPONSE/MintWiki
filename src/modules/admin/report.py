"""관리자 활동 보고 도메인 모델."""
from datetime import datetime
from typing import Optional


class EmptyAdminReportIdError(Exception):
    """보고서 id가 비어있을 때 발생."""

    pass


class AdminReport:
    """
    관리자의 활동을 기록한 보고서를 나타내는 도메인 모델.

    보고서는 특정 시간 기간 동안 이루어진 관리자 활동
    (차단, 보호 등)을 집계하여 나타낸다. 보고서는 생성된 시각과
    생성을 수행한 관리자의 id를 가진다.
    """

    def __init__(
        self,
        id: str,
        generated_at: datetime,
        actor_id: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
    ):
        """
        관리자 활동 보고서를 생성한다.

        Args:
            id: 보고서의 고유 식별자
            generated_at: 보고서가 생성된 시각
            actor_id: 보고서를 생성한 관리자의 id (선택사항)
            start_at: 보고서가 포함하는 기간의 시작 시각 (선택사항)
            end_at: 보고서가 포함하는 기간의 종료 시각 (선택사항)

        Raises:
            EmptyAdminReportIdError: 보고서 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyAdminReportIdError("보고서 id는 비어있을 수 없습니다")

        self.id = id
        self.generated_at = generated_at
        self.actor_id = actor_id
        self.start_at = start_at
        self.end_at = end_at
