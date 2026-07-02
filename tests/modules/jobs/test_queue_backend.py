"""잡 큐 백엔드 인터페이스 테스트."""
from collections import deque
from typing import Optional

import pytest

from modules.jobs.payload import JobPayload
from modules.jobs.queue_backend import QueueBackend


class SamplePayload(JobPayload):
    def __init__(self, name: str):
        self.name = name

    @property
    def job_type(self) -> str:
        return "sample.job"


class ConcreteQueueBackend(QueueBackend):
    """테스트용 구체적인 FIFO 메모리 큐 백엔드 구현."""

    def __init__(self):
        """빈 큐를 초기화한다."""
        self._items: deque[JobPayload] = deque()

    async def enqueue(self, payload: JobPayload) -> None:
        """잡 페이로드를 큐에 적재한다."""
        self._items.append(payload)

    async def dequeue(self) -> Optional[JobPayload]:
        """큐에서 다음 잡 페이로드를 꺼낸다."""
        if not self._items:
            return None
        return self._items.popleft()

    async def size(self) -> int:
        """큐에 남아 있는 잡 페이로드 개수를 반환한다."""
        return len(self._items)


class TestQueueBackendInterface:
    """잡 큐 백엔드 인터페이스 테스트."""

    def test_backend_is_abstract(self):
        """큐 백엔드는 추상 클래스이다."""
        with pytest.raises(TypeError):
            QueueBackend()

    def test_enqueue_method_exists(self):
        """큐 백엔드는 enqueue 메서드를 정의한다."""
        assert hasattr(QueueBackend, "enqueue")

    def test_dequeue_method_exists(self):
        """큐 백엔드는 dequeue 메서드를 정의한다."""
        assert hasattr(QueueBackend, "dequeue")

    def test_size_method_exists(self):
        """큐 백엔드는 size 메서드를 정의한다."""
        assert hasattr(QueueBackend, "size")

    @pytest.mark.asyncio
    async def test_dequeue_on_empty_queue_returns_none(self):
        """비어 있는 큐에서 꺼내면 None을 반환한다."""
        backend = ConcreteQueueBackend()

        result = await backend.dequeue()

        assert result is None

    @pytest.mark.asyncio
    async def test_enqueue_then_dequeue_returns_same_payload(self):
        """적재한 페이로드를 그대로 꺼낼 수 있다."""
        backend = ConcreteQueueBackend()
        payload = SamplePayload("first")

        await backend.enqueue(payload)
        result = await backend.dequeue()

        assert result is payload

    @pytest.mark.asyncio
    async def test_dequeue_returns_payloads_in_fifo_order(self):
        """여러 페이로드를 적재하면 적재한 순서대로 꺼낼 수 있다."""
        backend = ConcreteQueueBackend()
        first = SamplePayload("first")
        second = SamplePayload("second")

        await backend.enqueue(first)
        await backend.enqueue(second)

        assert await backend.dequeue() is first
        assert await backend.dequeue() is second

    @pytest.mark.asyncio
    async def test_size_reflects_number_of_enqueued_payloads(self):
        """size는 큐에 남아 있는 페이로드 개수를 반환한다."""
        backend = ConcreteQueueBackend()

        assert await backend.size() == 0

        await backend.enqueue(SamplePayload("first"))
        await backend.enqueue(SamplePayload("second"))

        assert await backend.size() == 2

    @pytest.mark.asyncio
    async def test_size_decreases_after_dequeue(self):
        """dequeue 후에는 size가 줄어든다."""
        backend = ConcreteQueueBackend()
        await backend.enqueue(SamplePayload("first"))

        await backend.dequeue()

        assert await backend.size() == 0
