"""RQ 백엔드 구현 테스트."""
import json
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.jobs.payload import JobPayload
from modules.jobs.rq_backend import RQQueueBackend


class SamplePayload(JobPayload):
    def __init__(self, name: str):
        self.name = name

    @property
    def job_type(self) -> str:
        return "sample.job"


class TestRQQueueBackend:
    """RQ 큐 백엔드 구현 테스트."""

    @pytest.fixture
    def mock_redis(self):
        """모의 Redis 클라이언트를 생성한다."""
        return AsyncMock()

    @pytest.fixture
    def rq_backend(self, mock_redis):
        """RQ 백엔드 인스턴스를 생성한다."""
        return RQQueueBackend(redis_client=mock_redis, queue_name="jobs")

    def test_rq_backend_initializes_with_queue_name(self, mock_redis):
        """RQ 백엔드는 큐 이름으로 초기화된다."""
        backend = RQQueueBackend(redis_client=mock_redis, queue_name="test_queue")

        assert backend.queue_name == "test_queue"
        assert backend.redis is mock_redis

    def test_rq_backend_uses_default_queue_name(self, mock_redis):
        """RQ 백엔드는 기본 큐 이름을 사용한다."""
        backend = RQQueueBackend(redis_client=mock_redis)

        assert backend.queue_name == "jobs"

    @pytest.mark.asyncio
    async def test_enqueue_calls_redis_rpush(self, rq_backend, mock_redis):
        """enqueue는 Redis의 RPUSH를 호출한다."""
        payload = SamplePayload("test")
        mock_redis.rpush = AsyncMock()

        await rq_backend.enqueue(payload)

        mock_redis.rpush.assert_called_once()
        args = mock_redis.rpush.call_args[0]
        assert args[0] == "rq:queue:jobs"

    @pytest.mark.asyncio
    async def test_dequeue_calls_redis_lpop(self, rq_backend, mock_redis):
        """dequeue는 Redis의 LPOP을 호출한다."""
        # 역직렬화 불가능하지만 Redis 호출 확인용
        mock_redis.lpop = AsyncMock(return_value=None)

        result = await rq_backend.dequeue()

        mock_redis.lpop.assert_called_once_with("rq:queue:jobs")

    @pytest.mark.asyncio
    async def test_dequeue_returns_none_when_queue_empty(
        self, rq_backend, mock_redis
    ):
        """큐가 비어 있을 때 dequeue는 None을 반환한다."""
        mock_redis.lpop = AsyncMock(return_value=None)

        result = await rq_backend.dequeue()

        assert result is None

    @pytest.mark.asyncio
    async def test_size_calls_redis_llen(self, rq_backend, mock_redis):
        """size는 Redis의 LLEN을 호출한다."""
        mock_redis.llen = AsyncMock(return_value=5)

        result = await rq_backend.size()

        mock_redis.llen.assert_called_once_with("rq:queue:jobs")
        assert result == 5

    @pytest.mark.asyncio
    async def test_size_returns_zero_when_empty(self, rq_backend, mock_redis):
        """큐가 비어 있을 때 size는 0을 반환한다."""
        mock_redis.llen = AsyncMock(return_value=None)

        result = await rq_backend.size()

        assert result == 0

    def test_serialize_payload_creates_json_with_job_type(self, rq_backend):
        """serialize_payload는 job_type을 포함하는 JSON을 생성한다."""
        payload = SamplePayload("test")

        result = rq_backend._serialize_payload(payload)

        data = json.loads(result)
        assert data["job_type"] == "sample.job"

    def test_serialize_payload_creates_json_with_data(self, rq_backend):
        """serialize_payload는 data를 포함하는 JSON을 생성한다."""
        payload = SamplePayload("test")

        result = rq_backend._serialize_payload(payload)

        data = json.loads(result)
        assert "data" in data

    def test_deserialize_payload_raises_not_implemented(self, rq_backend):
        """deserialize_payload는 NotImplementedError를 발생한다."""
        json_str = json.dumps({"job_type": "sample.job", "data": {}})

        with pytest.raises(NotImplementedError):
            rq_backend._deserialize_payload(json_str)

    def test_extract_payload_data_returns_non_private_attributes(
        self, rq_backend
    ):
        """extract_payload_data는 비공개 속성을 제외한 모든 속성을 반환한다."""
        payload = SamplePayload("test")

        result = rq_backend._extract_payload_data(payload)

        assert "name" in result
        assert result["name"] == "test"

    def test_rq_backend_queue_key_format(self, rq_backend):
        """RQ 백엔드는 올바른 Redis 키 포맷을 사용한다."""
        assert rq_backend._queue_key == "rq:queue:jobs"

        backend_with_custom_name = RQQueueBackend(
            redis_client=AsyncMock(), queue_name="custom"
        )
        assert backend_with_custom_name._queue_key == "rq:queue:custom"
