"""잡 ID 생성 모듈."""
import uuid


def generate_job_id() -> str:
    """
    새로운 잡 ID를 생성한다.

    UUID4를 기반으로 한 고유한 문자열 ID를 생성한다. 감사 이벤트, 잡 인스턴스,
    또는 잡 추적이 필요한 모든 곳에서 사용할 수 있다.

    Returns:
        UUID4 형식의 고유한 잡 ID
    """
    return str(uuid.uuid4())


__all__ = ["generate_job_id"]
