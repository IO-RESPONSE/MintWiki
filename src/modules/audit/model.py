"""감사 이벤트 도메인 모델."""
from datetime import datetime
from typing import Optional


class EmptyAuditEventIdError(Exception):
    """감사 이벤트 id가 비어있을 때 발생."""

    pass


class MissingEventTypeError(Exception):
    """감사 이벤트의 event_type이 비어있을 때 발생."""

    pass


class MissingActionError(Exception):
    """감사 이벤트의 action이 비어있을 때 발생."""

    pass


class MissingResourceIdError(Exception):
    """감사 이벤트가 참조하는 resource_id가 비어있을 때 발생."""

    pass


class AuditEvent:
    """
    감사 이벤트를 나타내는 도메인 모델.

    이벤트는 특정 리소스(resource_id)에 대해 어떤 동작(action)이 일어났는지를
    기록하며, 해당 리소스의 종류(event_type), 누가 변경했는지(actor_id)를
    함께 담아 상위 호출자가 변경 이력을 추적할 수 있게 한다.
    이벤트를 언제 기록할지(변경 시점에 실제로 남기는 로직)와 영속화
    방법은 이 모델이 아닌 상위 서비스가 담당한다.
    """

    def __init__(
        self,
        id: str,
        event_type: str,
        action: str,
        resource_id: str,
        occurred_at: datetime,
        actor_id: Optional[str] = None,
    ):
        """
        감사 이벤트를 생성한다.

        Args:
            id: 감사 이벤트의 고유 식별자
            event_type: 이벤트의 종류 (e.g., "document", "admin", "permission")
            action: 이벤트가 기록하는 동작 (e.g., "created", "updated", "deleted")
            resource_id: 변경이 발생한 리소스의 id
            occurred_at: 변경이 발생한 시각
            actor_id: 변경을 수행한 사용자의 id (선택사항)

        Raises:
            EmptyAuditEventIdError: 이벤트 id가 비어있거나 공백만 있는 경우
            MissingEventTypeError: event_type이 비어있거나 공백만 있는 경우
            MissingActionError: action이 비어있거나 공백만 있는 경우
            MissingResourceIdError: resource_id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyAuditEventIdError("감사 이벤트 id는 비어있을 수 없습니다")
        if not event_type or not event_type.strip():
            raise MissingEventTypeError("event_type은 비어있을 수 없습니다")
        if not action or not action.strip():
            raise MissingActionError("action은 비어있을 수 없습니다")
        if not resource_id or not resource_id.strip():
            raise MissingResourceIdError("resource_id는 비어있을 수 없습니다")

        self.id = id
        self.event_type = event_type
        self.action = action
        self.resource_id = resource_id
        self.occurred_at = occurred_at
        self.actor_id = actor_id


__all__ = [
    "AuditEvent",
    "EmptyAuditEventIdError",
    "MissingEventTypeError",
    "MissingActionError",
    "MissingResourceIdError",
]
