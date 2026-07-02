"""감사 이벤트 저장소 인터페이스 및 구현."""
from abc import ABC, abstractmethod
from typing import List, Optional

from modules.audit.model import AuditEvent


class AuditRepository(ABC):
    """
    감사 이벤트 저장소의 인터페이스.

    저장소는 감사 이벤트를 저장하고 검색하는 메서드를 정의한다.
    구체적인 저장소 구현(메모리, 데이터베이스 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def create(self, event: AuditEvent) -> AuditEvent:
        """
        새로운 감사 이벤트를 저장소에 저장한다.

        Args:
            event: 저장할 감사 이벤트

        Returns:
            저장된 감사 이벤트

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[AuditEvent]:
        """
        주어진 id로 감사 이벤트를 조회한다.

        Args:
            id: 조회할 감사 이벤트의 고유 식별자

        Returns:
            조회된 감사 이벤트 또는 없으면 None
        """
        pass

    @abstractmethod
    async def get_by_resource_id(self, resource_id: str) -> List[AuditEvent]:
        """
        주어진 리소스 id로 감사 이벤트들을 조회한다.

        Args:
            resource_id: 조회할 리소스의 고유 식별자

        Returns:
            조회된 감사 이벤트의 리스트 (없으면 빈 리스트)
        """
        pass

    @abstractmethod
    async def list_all(self) -> List[AuditEvent]:
        """
        저장소에 저장된 모든 감사 이벤트를 조회한다.

        Returns:
            모든 감사 이벤트의 리스트 (없으면 빈 리스트)
        """
        pass


class InMemoryAuditRepository(AuditRepository):
    """
    메모리에 감사 이벤트를 저장하는 저장소 구현.

    초기 테스트 및 개발 단계에서 사용하기 위한 메모리 기반
    저장소 구현이다.
    """

    def __init__(self):
        """저장소를 초기화한다."""
        self.events: dict[str, AuditEvent] = {}
        self.resource_id_index: dict[str, list[str]] = {}

    async def create(self, event: AuditEvent) -> AuditEvent:
        """
        새로운 감사 이벤트를 저장소에 저장한다.

        Args:
            event: 저장할 감사 이벤트

        Returns:
            저장된 감사 이벤트
        """
        self.events[event.id] = event

        if event.resource_id not in self.resource_id_index:
            self.resource_id_index[event.resource_id] = []
        self.resource_id_index[event.resource_id].append(event.id)

        return event

    async def get(self, id: str) -> Optional[AuditEvent]:
        """
        주어진 id로 감사 이벤트를 조회한다.

        Args:
            id: 조회할 감사 이벤트의 고유 식별자

        Returns:
            조회된 감사 이벤트 또는 없으면 None
        """
        return self.events.get(id)

    async def get_by_resource_id(self, resource_id: str) -> List[AuditEvent]:
        """
        주어진 리소스 id로 감사 이벤트들을 조회한다.

        Args:
            resource_id: 조회할 리소스의 고유 식별자

        Returns:
            조회된 감사 이벤트의 리스트 (없으면 빈 리스트)
        """
        event_ids = self.resource_id_index.get(resource_id, [])
        return [self.events[event_id] for event_id in event_ids]

    async def list_all(self) -> List[AuditEvent]:
        """
        저장소에 저장된 모든 감사 이벤트를 조회한다.

        Returns:
            모든 감사 이벤트의 리스트 (없으면 빈 리스트)
        """
        return list(self.events.values())
