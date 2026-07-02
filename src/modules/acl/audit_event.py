"""ACL 감사 이벤트 도메인 모델."""
from datetime import datetime
from enum import Enum
from typing import Optional


class AclAuditAction(Enum):
    """
    ACL 감사 이벤트가 기록하는 변경 동작의 종류.
    """

    RULE_ADDED = "rule_added"
    RULE_REMOVED = "rule_removed"


class EmptyAclAuditEventIdError(Exception):
    """감사 이벤트 id가 비어있을 때 발생."""

    pass


class MissingRuleIdError(Exception):
    """감사 이벤트가 참조하는 규칙 id가 비어있을 때 발생."""

    pass


class AclAuditEvent:
    """
    문서 ACL 규칙 변경 내역을 기록하는 감사 이벤트 도메인 모델.

    이벤트는 어떤 규칙(rule_id)에 어떤 동작(action)이 일어났는지를
    기록하며, 어느 문서에 대한 변경인지(document_id), 누가 변경했는지
    (actor_id)를 함께 담아 상위 호출자가 변경 이력을 추적할 수 있게
    한다. 이벤트를 언제 기록할지(ACL 변경 시점에 실제로 남기는 로직)와
    영속화 방법은 이 모델이 아닌 상위 서비스가 담당한다.
    """

    def __init__(
        self,
        id: str,
        action: AclAuditAction,
        rule_id: str,
        occurred_at: datetime,
        document_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ):
        """
        ACL 감사 이벤트를 생성한다.

        Args:
            id: 감사 이벤트의 고유 식별자
            action: 이벤트가 기록하는 변경 동작의 종류
            rule_id: 변경이 발생한 ACL 규칙의 id
            occurred_at: 변경이 발생한 시각
            document_id: 변경이 적용된 문서의 id (선택사항)
            actor_id: 변경을 수행한 사용자의 id (선택사항)

        Raises:
            EmptyAclAuditEventIdError: 이벤트 id가 비어있거나 공백만 있는 경우
            MissingRuleIdError: 규칙 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyAclAuditEventIdError("감사 이벤트 id는 비어있을 수 없습니다")
        if not rule_id or not rule_id.strip():
            raise MissingRuleIdError("규칙 id는 비어있을 수 없습니다")

        self.id = id
        self.action = action
        self.rule_id = rule_id
        self.occurred_at = occurred_at
        self.document_id = document_id
        self.actor_id = actor_id

    def is_rule_added(self) -> bool:
        """이벤트가 규칙 추가를 기록하는지 확인한다."""
        return self.action is AclAuditAction.RULE_ADDED

    def is_rule_removed(self) -> bool:
        """이벤트가 규칙 제거를 기록하는지 확인한다."""
        return self.action is AclAuditAction.RULE_REMOVED
