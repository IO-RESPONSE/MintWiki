"""파서 도메인 모델."""
from typing import Any, Dict, List


class ParserResult:
    """
    파싱 결과를 나타내는 도메인 모델.

    파서가 소스 텍스트를 파싱한 후 생성하는 중간 표현이다.
    블록 단위의 파싱 결과와 추출된 메타데이터를 포함한다.
    """

    def __init__(
        self,
        blocks: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ):
        """
        파싱 결과를 생성한다.

        Args:
            blocks: 파싱된 블록 요소들의 리스트
            metadata: 파싱 중에 추출된 메타데이터
                - links: 문서에서 추출된 링크 목록
                - categories: 문서의 카테고리 목록
                - redirects: 리다이렉트 정보
                - headings: 제목 목록
                - transclusions: 트랜스클루전 목록
        """
        self.blocks = blocks
        self.metadata = metadata
