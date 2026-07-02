"""관리자 차단 관리 서비스."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from modules.admin.audit_event import AdminBlockAuditAction, AdminBlockAuditEvent
from modules.user.block import Block
from modules.user.block_repository import BlockRepository


class AdminBlockService:
    """
    관리자가 사용자 차단을 생성하고 관리하는 서비스.

    차단을 생성하거나 삭제할 때 이 서비스를 통해 변경을 수행하면,
    실제 차단 저장소에 변경을 반영함과 동시에 그 변경 내용을 담은
    AdminBlockAuditEvent를 생성해 메모리에 누적한다. 이벤트의
    영속화(저장소 연동)는 이 서비스가 아닌 이후 태스크에서 다룬다.
    """

    def __init__(self, block_repository: BlockRepository):
        """
        서비스를 초기화한다.

        Args:
            block_repository: 차단 저장소
        """
        self.block_repository = block_repository
        self._events: List[AdminBlockAuditEvent] = []

    async def create_block(
        self,
        user_id: str,
        reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        actor_id: Optional[str] = None,
    ) -> Block:
        """
        새로운 사용자 차단을 생성한다.

        차단을 생성하고 저장소에 저장한 후, 변경을 감사 이벤트로 기록한다.

        Args:
            user_id: 차단할 사용자의 id
            reason: 차단 사유 (선택사항)
            expires_at: 차단 만료 시각 (선택사항, None이면 무기한 차단)
            actor_id: 차단을 수행한 관리자의 id (선택사항)

        Returns:
            생성된 차단

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        block = Block(
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            reason=reason,
            blocked_by=actor_id,
        )
        created_block = await self.block_repository.create(block)
        self._append_event(
            action=AdminBlockAuditAction.BLOCK_CREATED,
            block_id=created_block.id,
            actor_id=actor_id,
        )
        return created_block

    async def delete_block(
        self,
        block_id: str,
        actor_id: Optional[str] = None,
    ) -> None:
        """
        차단을 삭제한다.

        저장소에서 차단을 삭제한 후, 변경을 감사 이벤트로 기록한다.

        Args:
            block_id: 삭제할 차단의 id
            actor_id: 삭제를 수행한 관리자의 id (선택사항)
        """
        await self.block_repository.delete(block_id)
        self._append_event(
            action=AdminBlockAuditAction.BLOCK_DELETED,
            block_id=block_id,
            actor_id=actor_id,
        )

    def events(self) -> List[AdminBlockAuditEvent]:
        """지금까지 기록된 감사 이벤트 목록을 시간 순서대로 반환한다."""
        return list(self._events)

    def _append_event(
        self,
        action: AdminBlockAuditAction,
        block_id: str,
        actor_id: Optional[str],
    ) -> AdminBlockAuditEvent:
        event = AdminBlockAuditEvent(
            id=str(uuid.uuid4()),
            action=action,
            block_id=block_id,
            occurred_at=datetime.now(timezone.utc),
            actor_id=actor_id,
        )
        self._events.append(event)
        return event
