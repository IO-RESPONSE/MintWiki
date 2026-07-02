"""렌더 결과 도메인 모델."""
from typing import Any, Dict


class RenderResult:
    """
    렌더링 결과를 나타내는 도메인 모델.

    렌더러가 파서 결과를 처리한 후 생성하는 결과이다.
    안전하게 이스케이프된 HTML과 렌더링 중에 추출된 메타데이터를 포함한다.
    """

    def __init__(
        self,
        html: str,
        metadata: Dict[str, Any],
    ):
        """
        렌더링 결과를 생성한다.

        Args:
            html: 렌더링된 HTML 문자열
            metadata: 렌더링 중에 추출된 메타데이터
                - headings: 제목 정보 목록
                - links: 링크 정보 목록
                - categories: 카테고리 정보 목록
        """
        self.html = html
        self.metadata = metadata
