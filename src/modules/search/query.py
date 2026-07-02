"""검색 질의 도메인 모델."""
from typing import Optional


class EmptySearchQueryTermError(Exception):
    """검색 질의어가 비어있을 때 발생."""

    pass


class InvalidSearchQueryLimitError(Exception):
    """검색 질의의 limit이 1 미만일 때 발생."""

    pass


class InvalidSearchQueryOffsetError(Exception):
    """검색 질의의 offset이 음수일 때 발생."""

    pass


class SearchQuery:
    """
    검색을 요청할 때 사용하는 질의 도메인 모델.

    사용자가 입력한 검색어와 페이지네이션 파라미터(limit, offset)를 감싸는
    값 객체로, 어댑터/서비스 계층에 전달되어 실제 검색을 수행하는 데 쓰인다.
    """

    def __init__(self, term: str, limit: Optional[int] = None, offset: int = 0):
        """
        검색 질의를 생성한다.

        Args:
            term: 검색어
            limit: 반환할 최대 결과 개수 (선택사항, 생략하면 제한 없음)
            offset: 건너뛸 결과 개수 (기본값 0)

        Raises:
            EmptySearchQueryTermError: term이 비어있거나 공백만 있는 경우
            InvalidSearchQueryLimitError: limit이 1 미만인 경우
            InvalidSearchQueryOffsetError: offset이 음수인 경우
        """
        if not term or not term.strip():
            raise EmptySearchQueryTermError("검색 질의어는 비어있을 수 없습니다")
        if limit is not None and limit < 1:
            raise InvalidSearchQueryLimitError("limit은 1 이상이어야 합니다")
        if offset < 0:
            raise InvalidSearchQueryOffsetError("offset은 음수일 수 없습니다")

        self.term = term
        self.limit = limit
        self.offset = offset
