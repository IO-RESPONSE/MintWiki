"""리비전 도메인 모델."""
from typing import Optional


class Revision:
    """
    문서 리비전을 나타내는 도메인 모델.

    각 리비전은 불변이며, 고유한 id, 문서 id, 소스 텍스트, 저자 id,
    선택적으로 부모 리비전 id와 편집 요약을 가진다.
    """

    def __init__(
        self,
        id: str,
        document_id: str,
        source: str,
        author_id: str,
        summary: str,
        parent_revision_id: Optional[str] = None,
    ):
        """
        리비전을 생성한다.

        Args:
            id: 리비전의 고유 식별자
            document_id: 문서의 고유 식별자
            source: 리비전의 소스 텍스트
            author_id: 저자의 id
            summary: 편집 요약
            parent_revision_id: 부모 리비전의 id (선택사항, 첫 리비전은 None)
        """
        self.id = id
        self.document_id = document_id
        self.source = source
        self.author_id = author_id
        self.summary = summary
        self.parent_revision_id = parent_revision_id
