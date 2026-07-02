"""백링크 갱신 잡 페이로드."""
from modules.jobs.payload import JobPayload

BACKLINK_REFRESH_JOB_TYPE = "backlink.refresh"


class InvalidBacklinkRefreshJobPayloadError(Exception):
    """백링크 갱신 페이로드 파라미터가 유효하지 않을 때 발생."""

    pass


class BacklinkRefreshJobPayload(JobPayload):
    """
    문서 저장 후 백링크 색인을 갱신하는 작업 큐에 전달되는 페이로드.

    page_name이 가리키는 문서의 링크가 변경되었으므로, 이 문서가
    참조하는 대상 문서들의 백링크 목록을 다시 계산해야 함을 잡 러너에
    전달한다. 실제로 백링크 색인을 갱신하는 핸들러는 후속 태스크에서
    추가되므로, 이 페이로드는 데이터 계약만 정의한다.
    """

    def __init__(self, page_name: str):
        """
        백링크 갱신 잡 페이로드를 생성한다.

        Args:
            page_name: 링크가 변경되어 백링크 색인을 다시 계산해야 하는
                문서 이름

        Raises:
            InvalidBacklinkRefreshJobPayloadError: page_name이 비어있거나
                공백만 있는 경우
        """
        if page_name is None or not page_name.strip():
            raise InvalidBacklinkRefreshJobPayloadError(
                "page_name은 비어있을 수 없습니다"
            )

        self._page_name = page_name

    @property
    def job_type(self) -> str:
        return BACKLINK_REFRESH_JOB_TYPE

    @property
    def page_name(self) -> str:
        return self._page_name


__all__ = [
    "BACKLINK_REFRESH_JOB_TYPE",
    "InvalidBacklinkRefreshJobPayloadError",
    "BacklinkRefreshJobPayload",
]
