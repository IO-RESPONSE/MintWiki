"""관리자 차단 감사 이벤트 도메인 모델."""
from datetime import datetime
from enum import Enum
from typing import Optional


class AdminBlockAuditAction(Enum):
    """
    관리자 차단 감사 이벤트가 기록하는 변경 동작의 종류.
    """

    BLOCK_CREATED = "block_created"
    BLOCK_DELETED = "block_deleted"


class EmptyAdminBlockAuditEventIdError(Exception):
    """감사 이벤트 id가 비어있을 때 발생."""

    pass


class MissingAdminBlockAuditEventBlockIdError(Exception):
    """감사 이벤트가 참조하는 차단 id가 비어있을 때 발생."""

    pass


class AdminBlockAuditEvent:
    """
    관리자의 차단 관리 변경 내역을 기록하는 감사 이벤트 도메인 모델.

    이벤트는 어떤 차단(block_id)에 어떤 동작(action)이 일어났는지를
    기록하며, 누가 변경했는지(actor_id)를 함께 담아 상위 호출자가
    변경 이력을 추적할 수 있게 한다. 이벤트를 언제 기록할지
    (변경 시점에 실제로 남기는 로직)와 영속화 방법은 이 모델이
    아닌 상위 서비스가 담당한다.
    """

    def __init__(
        self,
        id: str,
        action: AdminBlockAuditAction,
        block_id: str,
        occurred_at: datetime,
        actor_id: Optional[str] = None,
    ):
        """
        관리자 차단 감사 이벤트를 생성한다.

        Args:
            id: 감사 이벤트의 고유 식별자
            action: 이벤트가 기록하는 변경 동작의 종류
            block_id: 변경이 발생한 차단의 id
            occurred_at: 변경이 발생한 시각
            actor_id: 변경을 수행한 사용자의 id (선택사항)

        Raises:
            EmptyAdminBlockAuditEventIdError: 이벤트 id가 비어있거나 공백만 있는 경우
            MissingAdminBlockAuditEventBlockIdError: 차단 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyAdminBlockAuditEventIdError("감사 이벤트 id는 비어있을 수 없습니다")
        if not block_id or not block_id.strip():
            raise MissingAdminBlockAuditEventBlockIdError("차단 id는 비어있을 수 없습니다")

        self.id = id
        self.action = action
        self.block_id = block_id
        self.occurred_at = occurred_at
        self.actor_id = actor_id

    def is_block_created(self) -> bool:
        """이벤트가 차단 생성을 기록하는지 확인한다."""
        return self.action is AdminBlockAuditAction.BLOCK_CREATED

    def is_block_deleted(self) -> bool:
        """이벤트가 차단 삭제를 기록하는지 확인한다."""
        return self.action is AdminBlockAuditAction.BLOCK_DELETED
