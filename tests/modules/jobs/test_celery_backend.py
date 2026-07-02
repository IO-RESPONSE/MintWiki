"""Celery 백엔드 구현 테스트."""
import json
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.jobs.celery_backend import CeleryQueueBackend
from modules.jobs.payload import JobPayload


class SamplePayload(JobPayload):
    def __init__(self, name: str):
        self.name = name

    @property
    def job_type(self) -> str:
        return "sample.job"


class TestCeleryQueueBackend:
    """Celery 큐 백엔드 구현 테스트."""

    @pytest.fixture
    def mock_celery_app(self):
        """모의 Celery 애플리케이션을 생성한다."""
        return MagicMock()

    @pytest.fixture
    def celery_backend(self, mock_celery_app):
        """Celery 백엔드 인스턴스를 생성한다."""
        return CeleryQueueBackend(celery_app=mock_celery_app, queue_name="jobs")

    def test_celery_backend_initializes_with_queue_name(self, mock_celery_app):
        """Celery 백엔드는 큐 이름으로 초기화된다."""
        backend = CeleryQueueBackend(celery_app=mock_celery_app, queue_name="test_queue")

        assert backend.queue_name == "test_queue"
        assert backend.celery_app is mock_celery_app

    def test_celery_backend_uses_default_queue_name(self, mock_celery_app):
        """Celery 백엔드는 기본 큐 이름을 사용한다."""
        backend = CeleryQueueBackend(celery_app=mock_celery_app)

        assert backend.queue_name == "jobs"

    @pytest.mark.asyncio
    async def test_enqueue_calls_send_to_broker(self, celery_backend):
        """enqueue는 _send_to_broker를 호출한다."""
        payload = SamplePayload("test")
        celery_backend._send_to_broker = AsyncMock()

        await celery_backend.enqueue(payload)

        celery_backend._send_to_broker.assert_called_once()
        args = celery_backend._send_to_broker.call_args[0]
        # 첫 번째 인자가 직렬화된 문자열인지 확인
        assert isinstance(args[0], str)

    @pytest.mark.asyncio
    async def test_dequeue_calls_receive_from_broker(self, celery_backend):
        """dequeue는 _receive_from_broker를 호출한다."""
        celery_backend._receive_from_broker = AsyncMock(return_value=None)

        result = await celery_backend.dequeue()

        celery_backend._receive_from_broker.assert_called_once()
        assert result is None

    @pytest.mark.asyncio
    async def test_dequeue_returns_none_when_queue_empty(self, celery_backend):
        """큐가 비어 있을 때 dequeue는 None을 반환한다."""
        celery_backend._receive_from_broker = AsyncMock(return_value=None)

        result = await celery_backend.dequeue()

        assert result is None

    @pytest.mark.asyncio
    async def test_size_calls_get_queue_size(self, celery_backend):
        """size는 _get_queue_size를 호출한다."""
        celery_backend._get_queue_size = AsyncMock(return_value=5)

        result = await celery_backend.size()

        celery_backend._get_queue_size.assert_called_once()
        assert result == 5

    @pytest.mark.asyncio
    async def test_size_returns_zero_when_empty(self, celery_backend):
        """큐가 비어 있을 때 size는 0을 반환한다."""
        celery_backend._get_queue_size = AsyncMock(return_value=None)

        result = await celery_backend.size()

        assert result == 0

    def test_serialize_payload_creates_json_with_job_type(self, celery_backend):
        """serialize_payload는 job_type을 포함하는 JSON을 생성한다."""
        payload = SamplePayload("test")

        result = celery_backend._serialize_payload(payload)

        data = json.loads(result)
        assert data["job_type"] == "sample.job"

    def test_serialize_payload_creates_json_with_data(self, celery_backend):
        """serialize_payload는 data를 포함하는 JSON을 생성한다."""
        payload = SamplePayload("test")

        result = celery_backend._serialize_payload(payload)

        data = json.loads(result)
        assert "data" in data

    def test_deserialize_payload_raises_not_implemented(self, celery_backend):
        """deserialize_payload는 NotImplementedError를 발생한다."""
        json_str = json.dumps({"job_type": "sample.job", "data": {}})

        with pytest.raises(NotImplementedError):
            celery_backend._deserialize_payload(json_str)

    def test_extract_payload_data_returns_non_private_attributes(
        self, celery_backend
    ):
        """extract_payload_data는 비공개 속성을 제외한 모든 속성을 반환한다."""
        payload = SamplePayload("test")

        result = celery_backend._extract_payload_data(payload)

        assert "name" in result
        assert result["name"] == "test"

    @pytest.mark.asyncio
    async def test_send_to_broker_raises_not_implemented(self, celery_backend):
        """_send_to_broker는 NotImplementedError를 발생한다."""
        with pytest.raises(NotImplementedError):
            await celery_backend._send_to_broker("test_payload")

    @pytest.mark.asyncio
    async def test_receive_from_broker_raises_not_implemented(self, celery_backend):
        """_receive_from_broker는 NotImplementedError를 발생한다."""
        with pytest.raises(NotImplementedError):
            await celery_backend._receive_from_broker()

    @pytest.mark.asyncio
    async def test_get_queue_size_raises_not_implemented(self, celery_backend):
        """_get_queue_size는 NotImplementedError를 발생한다."""
        with pytest.raises(NotImplementedError):
            await celery_backend._get_queue_size()
