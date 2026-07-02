"""잡 감사 이벤트 도메인 모델."""
from datetime import datetime
from enum import Enum
from typing import Optional


class JobAuditAction(Enum):
    """
    잡 감사 이벤트가 기록하는 실행 결과의 종류.
    """

    JOB_SUCCEEDED = "job_succeeded"
    JOB_FAILED = "job_failed"


class EmptyJobAuditEventIdError(Exception):
    """감사 이벤트 id가 비어있을 때 발생."""

    pass


class MissingJobTypeError(Exception):
    """감사 이벤트가 참조하는 job_type이 비어있을 때 발생."""

    pass


class InvalidJobAuditEventError(Exception):
    """action과 error 조합이 모순될 때 발생."""

    pass


class JobAuditEvent:
    """
    잡 실행 결과(성공/실패)를 기록하는 감사 이벤트 도메인 모델.

    이벤트는 어떤 종류의 잡(job_type)이 어떤 결과(action)로 끝났는지를
    기록하며, 실패인 경우 사유(error)를 함께 담아 상위 호출자가 잡 실행
    이력을 추적할 수 있게 한다. 이벤트를 언제 기록할지(잡 실행 시점에
    실제로 남기는 로직)와 영속화 방법은 이 모델이 아닌 상위 서비스
    (후속 태스크의 잡 감사 기록기)가 담당한다.
    """

    def __init__(
        self,
        id: str,
        action: JobAuditAction,
        job_type: str,
        occurred_at: datetime,
        error: Optional[str] = None,
    ):
        """
        잡 감사 이벤트를 생성한다.

        Args:
            id: 감사 이벤트의 고유 식별자
            action: 이벤트가 기록하는 잡 실행 결과의 종류
            job_type: 실행된 잡의 종류를 식별하는 문자열
            occurred_at: 잡 실행이 끝난 시각
            error: 실패 사유 (JOB_FAILED일 때만 사용, 그 외에는 항상 None)

        Raises:
            EmptyJobAuditEventIdError: 이벤트 id가 비어있거나 공백만 있는 경우
            MissingJobTypeError: job_type이 비어있거나 공백만 있는 경우
            InvalidJobAuditEventError: JOB_FAILED인데 error가 없거나,
                JOB_SUCCEEDED인데 error가 있는 경우
        """
        if not id or not id.strip():
            raise EmptyJobAuditEventIdError("감사 이벤트 id는 비어있을 수 없습니다")
        if not job_type or not job_type.strip():
            raise MissingJobTypeError("job_type은 비어있을 수 없습니다")
        if action is JobAuditAction.JOB_FAILED and error is None:
            raise InvalidJobAuditEventError(
                "실패 이벤트는 error가 반드시 있어야 합니다"
            )
        if action is JobAuditAction.JOB_SUCCEEDED and error is not None:
            raise InvalidJobAuditEventError(
                "성공 이벤트는 error를 가질 수 없습니다"
            )

        self.id = id
        self.action = action
        self.job_type = job_type
        self.occurred_at = occurred_at
        self.error = error

    def is_succeeded(self) -> bool:
        """이벤트가 잡 성공을 기록하는지 확인한다."""
        return self.action is JobAuditAction.JOB_SUCCEEDED

    def is_failed(self) -> bool:
        """이벤트가 잡 실패를 기록하는지 확인한다."""
        return self.action is JobAuditAction.JOB_FAILED


__all__ = [
    "JobAuditAction",
    "EmptyJobAuditEventIdError",
    "MissingJobTypeError",
    "InvalidJobAuditEventError",
    "JobAuditEvent",
]
