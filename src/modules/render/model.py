"""렌더 결과 도메인 모델."""
from typing import Any, Dict, List, Optional


class Heading:
    """
    제목 메타데이터를 나타내는 도메인 모델.

    렌더링 중에 추출된 제목 정보를 구조화하여 저장한다.
    """

    def __init__(self, level: int, text: str, id: str):
        """
        제목 메타데이터를 생성한다.

        Args:
            level: 제목 레벨 (1-6)
            text: 제목 텍스트
            id: 제목의 HTML id 속성 값
        """
        self.level = level
        self.text = text
        self.id = id


class Footnote:
    """
    각주 메타데이터를 나타내는 도메인 모델.

    렌더링 중에 추출된 각주 정보를 구조화하여 저장한다.
    """

    def __init__(self, id: str, text: str):
        """
        각주 메타데이터를 생성한다.

        Args:
            id: 각주의 고유 식별자
            text: 각주의 텍스트 내용
        """
        self.id = id
        self.text = text


class RenderMetadata:
    """
    렌더링 중에 추출된 메타데이터를 나타내는 도메인 모델.

    렌더러가 HTML을 생성하는 과정에서 추출되는 제목, 링크, 카테고리, 각주 정보를 포함한다.
    """

    def __init__(
        self,
        headings: Optional[List[Heading]] = None,
        links: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        footnotes: Optional[List[Footnote]] = None,
    ):
        """
        렌더링 메타데이터를 생성한다.

        Args:
            headings: 제목 메타데이터 목록
            links: 링크 목록
            categories: 카테고리 목록
            footnotes: 각주 메타데이터 목록
        """
        self.headings = headings or []
        self.links = links or []
        self.categories = categories or []
        self.footnotes = footnotes or []


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
