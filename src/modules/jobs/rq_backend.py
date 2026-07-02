"""RQ(Redis Queue) 기반 잡 큐 백엔드 구현."""
import json
from typing import Optional

from modules.jobs.payload import JobPayload
from modules.jobs.queue_backend import QueueBackend


class RQQueueBackend(QueueBackend):
    """
    RQ(Redis Queue)를 사용하는 잡 큐 백엔드 구현.

    Redis를 기반으로 하는 RQ를 통해 잡 페이로드를 큐에 적재하고 꺼낸다.
    분산 환경에서 여러 워커 프로세스가 공유 큐를 사용할 수 있다.
    """

    def __init__(self, redis_client, queue_name: str = "jobs", registry=None):
        """
        RQ 큐 백엔드를 초기화한다.

        Args:
            redis_client: redis.Redis 클라이언트 인스턴스
            queue_name: RQ 큐의 이름 (기본값: "jobs")
            registry: RQ 레지스트리 인스턴스 (선택사항)
        """
        self.redis = redis_client
        self.queue_name = queue_name
        self.registry = registry
        self._queue_key = f"rq:queue:{queue_name}"

    async def enqueue(self, payload: JobPayload) -> None:
        """
        잡 페이로드를 RQ 큐에 적재한다.

        페이로드를 JSON으로 직렬화하여 Redis 목록에 추가한다.

        Args:
            payload: 적재할 잡 페이로드
        """
        # 페이로드 직렬화
        serialized = self._serialize_payload(payload)
        # Redis 목록에 추가 (RPUSH)
        await self.redis.rpush(self._queue_key, serialized)

    async def dequeue(self) -> Optional[JobPayload]:
        """
        RQ 큐에서 다음 잡 페이로드를 꺼낸다.

        Redis 목록에서 왼쪽끝(LPOP)으로 꺼낸다.

        Returns:
            적재된 순서상 다음 잡 페이로드, 큐가 비어 있으면 None
        """
        # Redis 목록에서 꺼내기 (LPOP)
        serialized = await self.redis.lpop(self._queue_key)

        if serialized is None:
            return None

        # 페이로드 역직렬화
        return self._deserialize_payload(serialized)

    async def size(self) -> int:
        """
        RQ 큐에 남아 있는 잡 페이로드 개수를 반환한다.

        Returns:
            큐에 적재되어 있는 잡 페이로드 개수
        """
        # Redis 목록의 길이를 조회
        length = await self.redis.llen(self._queue_key)
        return length or 0

    def _serialize_payload(self, payload: JobPayload) -> str:
        """
        잡 페이로드를 JSON 문자열로 직렬화한다.

        Args:
            payload: 직렬화할 잡 페이로드

        Returns:
            JSON 형식의 문자열
        """
        data = {
            "job_type": payload.job_type,
            "data": self._extract_payload_data(payload),
        }
        return json.dumps(data, ensure_ascii=False)

    def _deserialize_payload(self, json_str: str) -> JobPayload:
        """
        JSON 문자열을 잡 페이로드로 역직렬화한다.

        이 메서드는 기본 구현으로, 실제 페이로드 복원은 job_type을 기반으로
        적절한 페이로드 클래스의 팩토리 메서드나 레지스트리를 통해
        수행되어야 한다. 현재는 스켈레톤 구현으로 직렬화된 데이터의
        구조만 정의한다.

        Args:
            json_str: JSON 형식의 문자열

        Returns:
            역직렬화된 잡 페이로드

        Raises:
            NotImplementedError: 구체적인 페이로드 복원 로직이
                아직 구현되지 않음
        """
        data = json.loads(json_str)
        # 실제 페이로드 복원은 job_type과 data를 기반으로
        # 적절한 페이로드 클래스의 팩토리 메서드나 레지스트리를 통해
        # 수행되어야 한다. 후속 태스크에서 구현된다.
        raise NotImplementedError(
            "페이로드 역직렬화는 후속 태스크에서 구현되어야 합니다. "
            "job_type과 data를 기반으로 적절한 페이로드 클래스를 "
            "복원해야 합니다."
        )

    def _extract_payload_data(self, payload: JobPayload) -> dict:
        """
        잡 페이로드에서 직렬화할 데이터를 추출한다.

        이 메서드는 기본 구현으로, 페이로드의 모든 속성을
        딕셔너리로 변환한다. 구체적인 페이로드 클래스에서는
        필요에 따라 이 메서드를 오버라이드할 수 있다.

        Args:
            payload: 데이터를 추출할 잡 페이로드

        Returns:
            직렬화 가능한 딕셔너리
        """
        # 기본 구현: job_type을 제외한 모든 속성을 추출
        data = {}
        for key, value in payload.__dict__.items():
            if not key.startswith("_"):
                data[key] = value
        return data


__all__ = ["RQQueueBackend"]
