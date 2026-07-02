"""관리자 보호 관리 서비스."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from modules.admin.protection_audit_event import (
    AdminProtectionAuditAction,
    AdminProtectionAuditEvent,
)
from modules.document.protection import Protection
from modules.document.protection_repository import ProtectionRepository


class AdminProtectionService:
    """
    관리자가 문서 보호를 생성하고 관리하는 서비스.

    보호를 생성하거나 삭제할 때 이 서비스를 통해 변경을 수행하면,
    실제 보호 저장소에 변경을 반영함과 동시에 그 변경 내용을 담은
    AdminProtectionAuditEvent를 생성해 메모리에 누적한다. 이벤트의
    영속화(저장소 연동)는 이 서비스가 아닌 이후 태스크에서 다룬다.
    """

    def __init__(self, protection_repository: ProtectionRepository):
        """
        서비스를 초기화한다.

        Args:
            protection_repository: 보호 저장소
        """
        self.protection_repository = protection_repository
        self._events: List[AdminProtectionAuditEvent] = []

    async def create_protection(
        self,
        document_id: str,
        reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        actor_id: Optional[str] = None,
    ) -> Protection:
        """
        새로운 문서 보호를 생성한다.

        보호를 생성하고 저장소에 저장한 후, 변경을 감사 이벤트로 기록한다.

        Args:
            document_id: 보호할 문서의 id
            reason: 보호 사유 (선택사항)
            expires_at: 보호 만료 시각 (선택사항, None이면 무기한 보호)
            actor_id: 보호를 설정한 관리자의 id (선택사항)

        Returns:
            생성된 보호

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        protection = Protection(
            id=str(uuid.uuid4()),
            document_id=document_id,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            reason=reason,
            protected_by=actor_id,
        )
        created_protection = await self.protection_repository.create(protection)
        self._append_event(
            action=AdminProtectionAuditAction.PROTECTION_CREATED,
            protection_id=created_protection.id,
            actor_id=actor_id,
        )
        return created_protection

    async def delete_protection(
        self,
        protection_id: str,
        actor_id: Optional[str] = None,
    ) -> None:
        """
        보호를 삭제한다.

        저장소에서 보호를 삭제한 후, 변경을 감사 이벤트로 기록한다.

        Args:
            protection_id: 삭제할 보호의 id
            actor_id: 삭제를 수행한 관리자의 id (선택사항)
        """
        await self.protection_repository.delete(protection_id)
        self._append_event(
            action=AdminProtectionAuditAction.PROTECTION_DELETED,
            protection_id=protection_id,
            actor_id=actor_id,
        )

    def events(self) -> List[AdminProtectionAuditEvent]:
        """지금까지 기록된 감사 이벤트 목록을 시간 순서대로 반환한다."""
        return list(self._events)

    def _append_event(
        self,
        action: AdminProtectionAuditAction,
        protection_id: str,
        actor_id: Optional[str],
    ) -> AdminProtectionAuditEvent:
        event = AdminProtectionAuditEvent(
            id=str(uuid.uuid4()),
            action=action,
            protection_id=protection_id,
            occurred_at=datetime.now(timezone.utc),
            actor_id=actor_id,
        )
        self._events.append(event)
        return event
