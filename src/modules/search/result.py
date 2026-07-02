"""검색 결과 도메인 모델."""
from modules.search.document import SearchDocument


class InvalidSearchResultScoreError(Exception):
    """검색 결과 점수가 음수일 때 발생."""

    pass


class SearchResult:
    """
    검색 질의에 대한 응답 항목 하나를 나타내는 도메인 모델.

    어댑터가 찾아낸 검색 문서(SearchDocument)와 그 문서의 관련도 점수를
    함께 담는다. 정렬/페이지네이션 등 결과 목록을 다루는 로직은
    후속 태스크에서 구현한다.
    """

    def __init__(self, document: SearchDocument, score: float):
        """
        검색 결과를 생성한다.

        Args:
            document: 검색된 문서
            score: 질의어와의 관련도 점수 (0 이상)

        Raises:
            InvalidSearchResultScoreError: score가 음수인 경우
        """
        if score < 0:
            raise InvalidSearchResultScoreError(
                "검색 결과 점수는 음수일 수 없습니다"
            )

        self.document = document
        self.score = score
