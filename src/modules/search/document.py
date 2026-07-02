"""검색 문서 도메인 모델."""
from typing import List, Optional


class EmptySearchDocumentIdError(Exception):
    """검색 문서 id가 비어있을 때 발생."""

    pass


class EmptySearchDocumentTitleError(Exception):
    """검색 문서 제목이 비어있을 때 발생."""

    pass


class SearchDocument:
    """
    검색 색인에 들어가는 문서를 나타내는 도메인 모델.

    원본 문서(Document)와 별개로, 검색 어댑터가 색인하고 조회하는 데
    필요한 최소한의 필드만 담는다. 제목/본문 검색과 리다이렉트 검색은
    이 모델을 바탕으로 후속 태스크에서 구현한다.
    """

    def __init__(
        self,
        document_id: str,
        title: str,
        body: str = "",
        redirect_target: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ):
        """
        검색 문서를 생성한다.

        Args:
            document_id: 원본 문서의 고유 식별자
            title: 검색 대상 제목
            body: 검색 대상 본문 텍스트 (기본값 빈 문자열)
            redirect_target: 리다이렉트 대상 문서의 id (선택사항, 리다이렉트 문서가 아니면 None)
            categories: 문서가 속한 카테고리명 목록 (선택사항, 기본값 빈 목록)

        Raises:
            EmptySearchDocumentIdError: document_id가 비어있거나 공백만 있는 경우
            EmptySearchDocumentTitleError: title이 비어있거나 공백만 있는 경우
        """
        if not document_id or not document_id.strip():
            raise EmptySearchDocumentIdError("검색 문서 id는 비어있을 수 없습니다")
        if not title or not title.strip():
            raise EmptySearchDocumentTitleError("검색 문서 제목은 비어있을 수 없습니다")

        self.document_id = document_id
        self.title = title
        self.body = body
        self.redirect_target = redirect_target
        self.categories = categories or []

    def is_redirect(self) -> bool:
        """이 검색 문서가 리다이렉트 문서인지 확인한다."""
        return self.redirect_target is not None
