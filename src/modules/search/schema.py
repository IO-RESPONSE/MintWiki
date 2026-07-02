"""검색 API 스키마."""
from typing import List, Optional

from pydantic import BaseModel


class IndexDocumentRequest(BaseModel):
    """
    검색 색인 요청 스키마.

    SearchDocument 도메인 모델을 구성하는 데 필요한 필드를 그대로 담는다.
    이 스키마를 실제 색인 HTTP 라우트에 연결하는 작업은 후속 태스크에서
    이루어진다.
    """

    document_id: str
    title: str
    body: str = ""
    redirect_target: Optional[str] = None
    categories: List[str] = []


class SearchResultResponse(BaseModel):
    """검색 결과 항목 응답 스키마."""

    document_id: str
    title: str
    score: float


class SearchResponse(BaseModel):
    """검색 응답 스키마."""

    results: List[SearchResultResponse]


class SearchHealthResponse(BaseModel):
    """검색 헬스 체크 응답 스키마."""

    healthy: bool
