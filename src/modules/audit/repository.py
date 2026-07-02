"""감사 이벤트 저장소."""
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.audit.audit_event import AuditEvent
from modules.audit.model import (
    AuditEvent as LegacyAuditEvent,
    DuplicateAuditEventIdError,
)
from persistence.models import AuditEventORM


class AuditRepository(ABC):
    """
    기존 Python 코어 감사 이벤트 저장소 인터페이스.

    DB 트랙은 `DatabaseAuditRepository`를 추가하지만, main의 in-memory
    감사 저장소 계약은 사용자/관리 모듈 테스트에서 계속 사용한다.
    """

    @abstractmethod
    async def create(self, event: LegacyAuditEvent) -> LegacyAuditEvent:
        """새로운 감사 이벤트를 저장소에 저장한다."""
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[LegacyAuditEvent]:
        """주어진 id로 감사 이벤트를 조회한다."""
        pass

    @abstractmethod
    async def get_by_resource_id(self, resource_id: str) -> List[LegacyAuditEvent]:
        """주어진 리소스 id로 감사 이벤트들을 조회한다."""
        pass

    @abstractmethod
    async def list_all(self) -> List[LegacyAuditEvent]:
        """저장소에 저장된 모든 감사 이벤트를 조회한다."""
        pass


class InMemoryAuditRepository(AuditRepository):
    """메모리에 감사 이벤트를 저장하는 저장소 구현."""

    def __init__(self):
        """저장소를 초기화한다."""
        self.events: dict[str, LegacyAuditEvent] = {}
        self.resource_id_index: dict[str, list[str]] = {}

    async def create(self, event: LegacyAuditEvent) -> LegacyAuditEvent:
        """
        새로운 감사 이벤트를 저장소에 저장한다.

        감사 저장소는 append-only이므로 동일한 id의 이벤트가 이미 존재하면
        DuplicateAuditEventIdError를 발생시킨다.
        """
        if event.id in self.events:
            raise DuplicateAuditEventIdError(
                f"id '{event.id}'인 감사 이벤트가 이미 존재합니다"
            )

        self.events[event.id] = event

        if event.resource_id not in self.resource_id_index:
            self.resource_id_index[event.resource_id] = []
        self.resource_id_index[event.resource_id].append(event.id)

        return event

    async def get(self, id: str) -> Optional[LegacyAuditEvent]:
        """주어진 id로 감사 이벤트를 조회한다."""
        return self.events.get(id)

    async def get_by_resource_id(self, resource_id: str) -> List[LegacyAuditEvent]:
        """주어진 리소스 id로 감사 이벤트들을 조회한다."""
        event_ids = self.resource_id_index.get(resource_id, [])
        return [self.events[event_id] for event_id in event_ids]

    async def list_all(self) -> List[LegacyAuditEvent]:
        """저장소에 저장된 모든 감사 이벤트를 조회한다."""
        return list(self.events.values())


class DatabaseAuditRepository:
    """
    데이터베이스 백엔드를 사용하는 감사 이벤트 저장소.

    이 저장소는 감사 이벤트의 append-only 속성을 강제한다.
    생성된 이벤트는 수정하거나 삭제할 수 없으며, 오직 추가만 가능하다.
    """

    def __init__(self, session: AsyncSession):
        """
        저장소를 초기화한다.

        Args:
            session: 데이터베이스 세션
        """
        self.session = session

    async def append(self, event: AuditEvent) -> AuditEvent:
        """
        감사 이벤트를 추가한다.

        Args:
            event: 추가할 감사 이벤트

        Returns:
            추가된 감사 이벤트
        """
        orm_event = AuditEventORM.from_domain(event)
        self.session.add(orm_event)
        await self.session.flush()
        return orm_event.to_domain()

    async def get(self, event_id: str) -> Optional[AuditEvent]:
        """
        id로 감사 이벤트를 조회한다.

        Args:
            event_id: 조회할 이벤트의 id

        Returns:
            조회된 감사 이벤트, 또는 존재하지 않으면 None
        """
        stmt = select(AuditEventORM).where(AuditEventORM.id == event_id)
        result = await self.session.execute(stmt)
        orm_event = result.scalar_one_or_none()
        return orm_event.to_domain() if orm_event else None

    async def list_by_category(self, category: str) -> List[AuditEvent]:
        """
        카테고리별로 감사 이벤트를 조회한다.

        Args:
            category: 조회할 카테고리

        Returns:
            조회된 감사 이벤트 목록
        """
        stmt = (
            select(AuditEventORM)
            .where(AuditEventORM.category == category)
            .order_by(AuditEventORM.occurred_at, AuditEventORM.id)
        )
        result = await self.session.execute(stmt)
        orm_events = result.scalars().all()
        return [orm_event.to_domain() for orm_event in orm_events]

    async def list_by_entity_id(self, entity_id: str) -> List[AuditEvent]:
        """
        엔티티별로 감사 이벤트를 조회한다.

        Args:
            entity_id: 조회할 엔티티 id

        Returns:
            조회된 감사 이벤트 목록
        """
        stmt = (
            select(AuditEventORM)
            .where(AuditEventORM.entity_id == entity_id)
            .order_by(AuditEventORM.occurred_at, AuditEventORM.id)
        )
        result = await self.session.execute(stmt)
        orm_events = result.scalars().all()
        return [orm_event.to_domain() for orm_event in orm_events]
