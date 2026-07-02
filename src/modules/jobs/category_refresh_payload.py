"""카테고리 갱신 잡 페이로드."""
from modules.jobs.payload import JobPayload

CATEGORY_REFRESH_JOB_TYPE = "category.refresh"


class InvalidCategoryRefreshJobPayloadError(Exception):
    """카테고리 갱신 페이로드 파라미터가 유효하지 않을 때 발생."""

    pass


class CategoryRefreshJobPayload(JobPayload):
    """
    문서 저장 후 카테고리 색인을 갱신하는 작업 큐에 전달되는 페이로드.

    category_name이 가리키는 카테고리에 속한 문서 목록이 변경되었으므로,
    해당 카테고리의 색인을 다시 계산해야 함을 잡 러너에 전달한다. 실제로
    카테고리 색인을 갱신하는 핸들러는 후속 태스크에서 추가되므로, 이
    페이로드는 데이터 계약만 정의한다.
    """

    def __init__(self, category_name: str):
        """
        카테고리 갱신 잡 페이로드를 생성한다.

        Args:
            category_name: 소속 문서가 변경되어 색인을 다시 계산해야 하는
                카테고리 이름

        Raises:
            InvalidCategoryRefreshJobPayloadError: category_name이
                비어있거나 공백만 있는 경우
        """
        if category_name is None or not category_name.strip():
            raise InvalidCategoryRefreshJobPayloadError(
                "category_name은 비어있을 수 없습니다"
            )

        self._category_name = category_name

    @property
    def job_type(self) -> str:
        return CATEGORY_REFRESH_JOB_TYPE

    @property
    def category_name(self) -> str:
        return self._category_name


__all__ = [
    "CATEGORY_REFRESH_JOB_TYPE",
    "InvalidCategoryRefreshJobPayloadError",
    "CategoryRefreshJobPayload",
]
