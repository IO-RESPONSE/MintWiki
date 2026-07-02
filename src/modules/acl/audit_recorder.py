"""ACL 변경 시 감사 이벤트를 기록하는 서비스."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from modules.acl.audit_event import AclAuditAction, AclAuditEvent
from modules.acl.document_acl import DocumentAcl
from modules.acl.rule import Rule


class AclAuditRecorder:
    """
    문서 ACL 규칙 변경을 AclAuditEvent로 기록하는 서비스.

    문서 ACL에 규칙을 추가하거나 제거할 때 이 서비스를 통해 변경을
    수행하면, DocumentAcl에 실제 변경을 반영함과 동시에 그 변경 내용을
    담은 AclAuditEvent를 생성해 메모리에 누적한다. 이벤트의 영속화
    (저장소 연동)는 이 서비스가 아닌 이후 태스크에서 다룬다.
    """

    def __init__(self):
        self._events: List[AclAuditEvent] = []

    def record_rule_added(
        self,
        document_acl: DocumentAcl,
        rule: Rule,
        actor_id: Optional[str] = None,
    ) -> AclAuditEvent:
        """
        문서 ACL에 규칙을 추가하고 그 변경을 감사 이벤트로 기록한다.

        Args:
            document_acl: 규칙을 추가할 문서 ACL
            rule: 추가할 규칙
            actor_id: 변경을 수행한 사용자의 id (선택사항)

        Returns:
            기록된 감사 이벤트
        """
        document_acl.add_rule(rule)
        event = self._append_event(
            action=AclAuditAction.RULE_ADDED,
            rule_id=rule.id,
            document_id=document_acl.document_id,
            actor_id=actor_id,
        )
        return event

    def record_rule_removed(
        self,
        document_acl: DocumentAcl,
        rule_id: str,
        actor_id: Optional[str] = None,
    ) -> AclAuditEvent:
        """
        문서 ACL에서 규칙을 제거하고 그 변경을 감사 이벤트로 기록한다.

        Args:
            document_acl: 규칙을 제거할 문서 ACL
            rule_id: 제거할 규칙의 id
            actor_id: 변경을 수행한 사용자의 id (선택사항)

        Returns:
            기록된 감사 이벤트
        """
        document_acl.remove_rule(rule_id)
        event = self._append_event(
            action=AclAuditAction.RULE_REMOVED,
            rule_id=rule_id,
            document_id=document_acl.document_id,
            actor_id=actor_id,
        )
        return event

    def events(self) -> List[AclAuditEvent]:
        """지금까지 기록된 감사 이벤트 목록을 시간 순서대로 반환한다."""
        return list(self._events)

    def _append_event(
        self,
        action: AclAuditAction,
        rule_id: str,
        document_id: Optional[str],
        actor_id: Optional[str],
    ) -> AclAuditEvent:
        event = AclAuditEvent(
            id=str(uuid.uuid4()),
            action=action,
            rule_id=rule_id,
            occurred_at=datetime.now(timezone.utc),
            document_id=document_id,
            actor_id=actor_id,
        )
        self._events.append(event)
        return event
