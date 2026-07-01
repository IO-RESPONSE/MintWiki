"""문서 도메인 모델."""
from typing import Optional

from modules.document.title import normalize_title


class Document:
    """
    문서를 나타내는 도메인 모델.

    문서는 고유한 id, 원본 제목, 정규화된 제목, 그리고 선택적으로
    현재 리비전 id를 가진다.
    """

    def __init__(
        self,
        id: str,
        title: str,
        current_revision_id: Optional[str] = None,
    ):
        """
        문서를 생성한다.

        Args:
            id: 문서의 고유 식별자
            title: 문서의 제목
            current_revision_id: 현재 리비전의 id (선택사항, 기본값 None)

        Raises:
            EmptyTitleError: 제목이 비어있거나 공백만 있는 경우
        """
        self.id = id
        self.title = title
        self.normalized_title = normalize_title(title)
        self.current_revision_id = current_revision_id
