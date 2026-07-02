"""잡 큐 백엔드 인터페이스."""
from abc import ABC, abstractmethod
from typing import Optional

from modules.jobs.payload import JobPayload


class QueueBackend(ABC):
    """
    잡 큐 백엔드의 인터페이스.

    잡 페이로드를 큐에 적재하고 꺼내는 메서드를 정의한다. 메모리 큐,
    외부 메시지 브로커 등 구체적인 구현은 이 인터페이스를 구현해야 한다.
    실행기와 큐를 연결하는 로직, 재시도 시 재적재 등 나머지 계약은
    후속 태스크에서 다루며, 이 인터페이스는 적재/소비/크기 조회 계약만
    담당한다.
    """

    @abstractmethod
    async def enqueue(self, payload: JobPayload) -> None:
        """
        잡 페이로드를 큐에 적재한다.

        Args:
            payload: 적재할 잡 페이로드
        """
        pass

    @abstractmethod
    async def dequeue(self) -> Optional[JobPayload]:
        """
        큐에서 다음 잡 페이로드를 꺼낸다.

        Returns:
            적재된 순서상 다음 잡 페이로드, 큐가 비어 있으면 None
        """
        pass

    @abstractmethod
    async def size(self) -> int:
        """
        큐에 남아 있는 잡 페이로드 개수를 반환한다.

        Returns:
            큐에 적재되어 있는 잡 페이로드 개수
        """
        pass


__all__ = ["QueueBackend"]
