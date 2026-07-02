"""Celery 기반 잡 큐 백엔드 구현."""
import json
from typing import Optional

from modules.jobs.payload import JobPayload
from modules.jobs.queue_backend import QueueBackend


class CeleryQueueBackend(QueueBackend):
    """
    Celery를 사용하는 잡 큐 백엔드 구현.

    Celery를 통해 잡 페이로드를 큐에 적재하고 꺼낸다.
    분산 환경에서 여러 워커 프로세스가 공유 큐를 사용할 수 있다.
    """

    def __init__(self, celery_app, queue_name: str = "jobs"):
        """
        Celery 큐 백엔드를 초기화한다.

        Args:
            celery_app: Celery 애플리케이션 인스턴스
            queue_name: 큐의 이름 (기본값: "jobs")
        """
        self.celery_app = celery_app
        self.queue_name = queue_name

    async def enqueue(self, payload: JobPayload) -> None:
        """
        잡 페이로드를 Celery 큐에 적재한다.

        페이로드를 JSON으로 직렬화하여 Celery 큐에 추가한다.

        Args:
            payload: 적재할 잡 페이로드
        """
        # 페이로드 직렬화
        serialized = self._serialize_payload(payload)
        # Celery 큐에 메시지 발행
        # 실제 구현은 후속 태스크에서 완성된다.
        await self._send_to_broker(serialized)

    async def dequeue(self) -> Optional[JobPayload]:
        """
        Celery 큐에서 다음 잡 페이로드를 꺼낸다.

        Returns:
            적재된 순서상 다음 잡 페이로드, 큐가 비어 있으면 None
        """
        # 큐에서 메시지를 꺼낸다.
        # 실제 구현은 후속 태스크에서 완성된다.
        serialized = await self._receive_from_broker()

        if serialized is None:
            return None

        # 페이로드 역직렬화
        return self._deserialize_payload(serialized)

    async def size(self) -> int:
        """
        Celery 큐에 남아 있는 잡 페이로드 개수를 반환한다.

        Returns:
            큐에 적재되어 있는 잡 페이로드 개수
        """
        # 큐의 크기를 조회한다.
        # 실제 구현은 후속 태스크에서 완성된다.
        count = await self._get_queue_size()
        return count or 0

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

    async def _send_to_broker(self, serialized: str) -> None:
        """
        직렬화된 페이로드를 브로커에 전송한다.

        이 메서드는 브로커별 구현에 따라 다르며, 후속 태스크에서
        완성된다.

        Args:
            serialized: JSON 직렬화된 페이로드
        """
        # 실제 구현은 후속 태스크에서 브로커 선택과 함께 구현된다.
        raise NotImplementedError(
            "브로커 전송은 후속 태스크에서 구현되어야 합니다."
        )

    async def _receive_from_broker(self) -> Optional[str]:
        """
        브로커에서 다음 메시지를 받는다.

        이 메서드는 브로커별 구현에 따라 다르며, 후속 태스크에서
        완성된다.

        Returns:
            JSON 직렬화된 페이로드, 또는 None (브로커에 메시지가 없을 때)
        """
        # 실제 구현은 후속 태스크에서 브로커 선택과 함께 구현된다.
        raise NotImplementedError(
            "브로커 수신은 후속 태스크에서 구현되어야 합니다."
        )

    async def _get_queue_size(self) -> int:
        """
        브로커의 큐 크기를 조회한다.

        이 메서드는 브로커별 구현에 따라 다르며, 후속 태스크에서
        완성된다.

        Returns:
            큐에 있는 메시지 개수
        """
        # 실제 구현은 후속 태스크에서 브로커 선택과 함께 구현된다.
        raise NotImplementedError(
            "큐 크기 조회는 후속 태스크에서 구현되어야 합니다."
        )


__all__ = ["CeleryQueueBackend"]
