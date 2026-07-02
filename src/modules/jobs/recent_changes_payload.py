"""최근 변경 내역 잡 페이로드."""
from datetime import datetime

from modules.jobs.payload import JobPayload

RECENT_CHANGES_JOB_TYPE = "recent_changes.record"


class InvalidRecentChangesJobPayloadError(Exception):
    """최근 변경 내역 페이로드 파라미터가 유효하지 않을 때 발생."""

    pass


class RecentChangesJobPayload(JobPayload):
    """
    문서 편집 후 최근 변경 내역 목록에 기록하는 작업 큐에 전달되는 페이로드.

    page_name이 가리키는 문서가 author_id에 의해 occurred_at 시각에
    편집되었으며 summary가 그 변경 요약임을 잡 러너에 전달한다. 실제로
    최근 변경 내역을 기록하는 핸들러는 후속 태스크에서 추가되므로, 이
    페이로드는 데이터 계약만 정의한다.
    """

    def __init__(
        self,
        page_name: str,
        author_id: str,
        occurred_at: datetime,
        summary: str = "",
    ):
        """
        최근 변경 내역 잡 페이로드를 생성한다.

        Args:
            page_name: 편집되어 최근 변경 내역에 기록해야 하는 문서 이름
            author_id: 편집을 수행한 사용자의 id
            occurred_at: 편집이 발생한 시각
            summary: 편집 요약 (선택사항, 기본값 빈 문자열)

        Raises:
            InvalidRecentChangesJobPayloadError: page_name이 비어있거나
                공백만 있는 경우, 또는 occurred_at이 주어지지 않은 경우
        """
        if page_name is None or not page_name.strip():
            raise InvalidRecentChangesJobPayloadError(
                "page_name은 비어있을 수 없습니다"
            )
        if occurred_at is None:
            raise InvalidRecentChangesJobPayloadError(
                "occurred_at은 비어있을 수 없습니다"
            )

        self._page_name = page_name
        self._author_id = author_id
        self._occurred_at = occurred_at
        self._summary = summary

    @property
    def job_type(self) -> str:
        return RECENT_CHANGES_JOB_TYPE

    @property
    def page_name(self) -> str:
        return self._page_name

    @property
    def author_id(self) -> str:
        return self._author_id

    @property
    def occurred_at(self) -> datetime:
        return self._occurred_at

    @property
    def summary(self) -> str:
        return self._summary

    @classmethod
    def from_dict(cls, data: dict) -> "RecentChangesJobPayload":
        """
        딕셔너리에서 최근 변경 내역 페이로드를 복원한다.

        Args:
            data: 페이로드 데이터를 담은 딕셔너리

        Returns:
            복원된 RecentChangesJobPayload 인스턴스
        """
        occurred_at = data["occurred_at"]
        # ISO 형식의 문자열을 datetime으로 변환
        if isinstance(occurred_at, str):
            occurred_at = datetime.fromisoformat(occurred_at)

        return cls(
            page_name=data["page_name"],
            author_id=data["author_id"],
            occurred_at=occurred_at,
            summary=data.get("summary", ""),
        )


__all__ = [
    "RECENT_CHANGES_JOB_TYPE",
    "InvalidRecentChangesJobPayloadError",
    "RecentChangesJobPayload",
]
