"""문서 색인 작업(job) 페이로드."""
from typing import List, Optional

from modules.search.document import SearchDocument


class IndexDocumentJobPayload:
    """
    문서 색인 작업 큐에 전달되는 페이로드.

    SearchDocument를 구성하는 데 필요한 필드를 그대로 담아, 잡 러너가
    비동기로 색인 작업을 처리할 수 있게 한다. 필드 유효성 검증은
    SearchDocument에 위임하므로 별도의 오류 타입을 두지 않는다. jobs
    모듈의 공통 페이로드 기반 클래스와 실제 잡 핸들러는 후속 태스크에서
    추가되므로, 지금은 이 페이로드만 독립적으로 정의한다.
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
        문서 색인 작업 페이로드를 생성한다.

        Args:
            document_id: 색인 대상 문서의 고유 식별자
            title: 색인 대상 제목
            body: 색인 대상 본문 텍스트 (기본값 빈 문자열)
            redirect_target: 리다이렉트 대상 문서의 id (선택사항)
            categories: 문서가 속한 카테고리명 목록 (선택사항, 기본값 빈 목록)

        Raises:
            EmptySearchDocumentIdError: document_id가 비어있거나 공백만 있는 경우
            EmptySearchDocumentTitleError: title이 비어있거나 공백만 있는 경우
        """
        self._document = SearchDocument(
            document_id=document_id,
            title=title,
            body=body,
            redirect_target=redirect_target,
            categories=categories,
        )

    @property
    def document_id(self) -> str:
        return self._document.document_id

    @property
    def title(self) -> str:
        return self._document.title

    @property
    def body(self) -> str:
        return self._document.body

    @property
    def redirect_target(self) -> Optional[str]:
        return self._document.redirect_target

    @property
    def categories(self) -> List[str]:
        return self._document.categories

    def to_search_document(self) -> SearchDocument:
        """이 페이로드로부터 색인 대상 SearchDocument를 생성한다."""
        return self._document
