"""관리자 보호 감사 이벤트 도메인 모델."""
from datetime import datetime
from enum import Enum
from typing import Optional


class AdminProtectionAuditAction(Enum):
    """
    관리자 보호 감사 이벤트가 기록하는 변경 동작의 종류.
    """

    PROTECTION_CREATED = "protection_created"
    PROTECTION_DELETED = "protection_deleted"


class EmptyAdminProtectionAuditEventIdError(Exception):
    """감사 이벤트 id가 비어있을 때 발생."""

    pass


class MissingAdminProtectionAuditEventProtectionIdError(Exception):
    """감사 이벤트가 참조하는 보호 id가 비어있을 때 발생."""

    pass


class AdminProtectionAuditEvent:
    """
    관리자의 보호 관리 변경 내역을 기록하는 감사 이벤트 도메인 모델.

    이벤트는 어떤 보호(protection_id)에 어떤 동작(action)이 일어났는지를
    기록하며, 누가 변경했는지(actor_id)를 함께 담아 상위 호출자가
    변경 이력을 추적할 수 있게 한다. 이벤트를 언제 기록할지
    (변경 시점에 실제로 남기는 로직)와 영속화 방법은 이 모델이
    아닌 상위 서비스가 담당한다.
    """

    def __init__(
        self,
        id: str,
        action: AdminProtectionAuditAction,
        protection_id: str,
        occurred_at: datetime,
        actor_id: Optional[str] = None,
    ):
        """
        관리자 보호 감사 이벤트를 생성한다.

        Args:
            id: 감사 이벤트의 고유 식별자
            action: 이벤트가 기록하는 변경 동작의 종류
            protection_id: 변경이 발생한 보호의 id
            occurred_at: 변경이 발생한 시각
            actor_id: 변경을 수행한 사용자의 id (선택사항)

        Raises:
            EmptyAdminProtectionAuditEventIdError: 이벤트 id가 비어있거나 공백만 있는 경우
            MissingAdminProtectionAuditEventProtectionIdError: 보호 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyAdminProtectionAuditEventIdError("감사 이벤트 id는 비어있을 수 없습니다")
        if not protection_id or not protection_id.strip():
            raise MissingAdminProtectionAuditEventProtectionIdError("보호 id는 비어있을 수 없습니다")

        self.id = id
        self.action = action
        self.protection_id = protection_id
        self.occurred_at = occurred_at
        self.actor_id = actor_id

    def is_protection_created(self) -> bool:
        """이벤트가 보호 생성을 기록하는지 확인한다."""
        return self.action is AdminProtectionAuditAction.PROTECTION_CREATED

    def is_protection_deleted(self) -> bool:
        """이벤트가 보호 삭제를 기록하는지 확인한다."""
        return self.action is AdminProtectionAuditAction.PROTECTION_DELETED
