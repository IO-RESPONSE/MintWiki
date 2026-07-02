"""검색 API 스키마."""
from typing import List

from pydantic import BaseModel


class SearchResultResponse(BaseModel):
    """검색 결과 항목 응답 스키마."""

    document_id: str
    title: str
    score: float


class SearchResponse(BaseModel):
    """검색 응답 스키마."""

    results: List[SearchResultResponse]
