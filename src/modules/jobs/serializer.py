"""잡 페이로드 직렬화 지원."""
import json
from datetime import datetime
from typing import Callable, Dict, Type

from modules.jobs.payload import JobPayload


class UnknownPayloadTypeError(Exception):
    """등록되지 않은 job_type의 페이로드를 역직렬화할 때 발생."""

    pass


class PayloadRegistry:
    """
    job_type을 페이로드 클래스에 매핑하는 레지스트리.

    직렬화/역직렬화에 필요한 페이로드 타입들을 등록하고 조회하는 기능을
    제공한다. 각 페이로드 클래스는 from_dict 클래스 메서드를 구현해야
    역직렬화될 수 있다.
    """

    def __init__(self):
        """빈 페이로드 레지스트리를 생성한다."""
        self._payloads: Dict[str, Type[JobPayload]] = {}

    def register(self, job_type: str, payload_class: Type[JobPayload]) -> None:
        """
        페이로드 클래스를 job_type으로 등록한다.

        Args:
            job_type: 페이로드를 식별하는 job_type 문자열
            payload_class: 등록할 페이로드 클래스

        Raises:
            ValueError: 동일한 job_type이 이미 등록된 경우
        """
        if job_type in self._payloads:
            raise ValueError(f"이미 등록된 job_type입니다: {job_type}")
        self._payloads[job_type] = payload_class

    def get(self, job_type: str) -> Type[JobPayload]:
        """
        job_type에 해당하는 페이로드 클래스를 조회한다.

        Args:
            job_type: 조회할 job_type 문자열

        Returns:
            등록된 페이로드 클래스

        Raises:
            UnknownPayloadTypeError: 등록되지 않은 job_type인 경우
        """
        if job_type not in self._payloads:
            raise UnknownPayloadTypeError(
                f"등록되지 않은 job_type입니다: {job_type}"
            )
        return self._payloads[job_type]

    def is_registered(self, job_type: str) -> bool:
        """job_type이 등록되어 있는지 여부를 반환한다."""
        return job_type in self._payloads


class JobPayloadSerializer:
    """
    잡 페이로드를 JSON 직렬화/역직렬화하는 유틸리티.

    페이로드를 JSON으로 직렬화하고, JSON을 다시 페이로드로 역직렬화한다.
    역직렬화에는 페이로드 레지스트리를 사용하여 job_type에 맞는 클래스를
    찾는다. 각 페이로드 클래스는 from_dict 클래스 메서드를 구현해야 한다.
    """

    @staticmethod
    def serialize(payload: JobPayload) -> str:
        """
        잡 페이로드를 JSON 문자열로 직렬화한다.

        Args:
            payload: 직렬화할 잡 페이로드

        Returns:
            JSON 형식의 문자열
        """
        data = {
            "job_type": payload.job_type,
            "data": JobPayloadSerializer._extract_payload_data(payload),
        }
        return json.dumps(data, ensure_ascii=False, default=JobPayloadSerializer._json_encoder)

    @staticmethod
    def deserialize(json_str: str, registry: PayloadRegistry) -> JobPayload:
        """
        JSON 문자열을 잡 페이로드로 역직렬화한다.

        Args:
            json_str: JSON 형식의 문자열
            registry: 페이로드 클래스를 조회할 레지스트리

        Returns:
            역직렬화된 잡 페이로드

        Raises:
            UnknownPayloadTypeError: 레지스트리에 등록되지 않은 job_type인 경우
        """
        data = json.loads(json_str)
        job_type = data["job_type"]
        payload_data = data["data"]

        payload_class = registry.get(job_type)
        return payload_class.from_dict(payload_data)

    @staticmethod
    def _extract_payload_data(payload: JobPayload) -> dict:
        """
        잡 페이로드에서 직렬화할 데이터를 추출한다.

        페이로드의 모든 공개 속성(비공개 속성 제외)을 추출한다. job_type은 제외한다.
        private 속성으로 저장된 데이터는 해당 공개 프로퍼티를 통해 접근한다.

        Args:
            payload: 데이터를 추출할 잡 페이로드

        Returns:
            직렬화 가능한 딕셔너리
        """
        data = {}

        # 클래스의 모든 프로퍼티(properties)를 찾아서 추출
        for attr_name in dir(type(payload)):
            # 비공개 속성이나 job_type은 제외
            if attr_name.startswith("_") or attr_name == "job_type":
                continue

            # 프로퍼티나 메서드인지 확인
            attr = getattr(type(payload), attr_name, None)
            if isinstance(attr, property):
                # 프로퍼티 값을 추출
                try:
                    data[attr_name] = getattr(payload, attr_name)
                except Exception:
                    # 접근 불가능한 프로퍼티는 제외
                    pass
            elif not callable(attr):
                # 공개 인스턴스 속성 추출
                try:
                    value = getattr(payload, attr_name)
                    if not callable(value):
                        data[attr_name] = value
                except Exception:
                    pass

        return data

    @staticmethod
    def _json_encoder(obj):
        """JSON 직렬화에서 기본 형식이 아닌 객체를 처리한다."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


__all__ = [
    "PayloadRegistry",
    "JobPayloadSerializer",
    "UnknownPayloadTypeError",
]
