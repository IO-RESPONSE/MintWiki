"""문서 API 스키마."""
from pydantic import BaseModel


class CreateDocumentRequest(BaseModel):
    """문서 생성 요청 스키마."""

    title: str
    source: str


class DocumentResponse(BaseModel):
    """문서 응답 스키마."""

    id: str
    title: str
