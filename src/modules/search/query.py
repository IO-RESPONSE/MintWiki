"""검색 질의 도메인 모델."""


class EmptySearchQueryTermError(Exception):
    """검색 질의어가 비어있을 때 발생."""

    pass


class SearchQuery:
    """
    검색을 요청할 때 사용하는 질의 도메인 모델.

    사용자가 입력한 검색어를 감싸는 최소한의 값 객체로,
    어댑터/서비스 계층에 전달되어 실제 검색을 수행하는 데 쓰인다.
    페이지네이션 등 추가 검색 파라미터는 후속 태스크에서 다룬다.
    """

    def __init__(self, term: str):
        """
        검색 질의를 생성한다.

        Args:
            term: 검색어

        Raises:
            EmptySearchQueryTermError: term이 비어있거나 공백만 있는 경우
        """
        if not term or not term.strip():
            raise EmptySearchQueryTermError("검색 질의어는 비어있을 수 없습니다")

        self.term = term
