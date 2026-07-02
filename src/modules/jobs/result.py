"""잡 실행 결과 모델."""
from typing import Any, Optional


class InvalidJobResultError(Exception):
    """success 값과 error/data 조합이 모순될 때 발생."""

    pass


class JobResult:
    """
    잡 핸들러가 한 번의 실행을 마친 뒤 반환하는 결과 값 객체.

    성공(success=True) 시에는 산출물을 data에, 실패(success=False) 시에는
    사유를 error에 담는다. 재시도 여부 판단이나 잡 상태 전이 등 나머지
    계약은 후속 태스크(잡 상태 enum, 잡 실행기 등)에서 다룬다.
    """

    def __init__(
        self,
        success: bool,
        data: Optional[Any] = None,
        error: Optional[str] = None,
    ):
        """
        잡 실행 결과를 생성한다.

        Args:
            success: 잡 실행 성공 여부
            data: 성공 시 산출물 (실패 시에는 항상 None)
            error: 실패 사유 (성공 시에는 항상 None)

        Raises:
            InvalidJobResultError: success=True인데 error가 있거나,
                success=False인데 error가 없는 경우
        """
        if success and error is not None:
            raise InvalidJobResultError(
                "성공한 잡 결과는 error를 가질 수 없습니다"
            )
        if not success and error is None:
            raise InvalidJobResultError(
                "실패한 잡 결과는 error가 반드시 있어야 합니다"
            )

        self.success = success
        self.data = data
        self.error = error

    @classmethod
    def ok(cls, data: Optional[Any] = None) -> "JobResult":
        """성공한 잡 실행 결과를 생성한다."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "JobResult":
        """실패한 잡 실행 결과를 생성한다."""
        return cls(success=False, error=error)
