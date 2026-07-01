"""리비전 API 스키마."""
from typing import Optional
from pydantic import BaseModel


class RevisionResponse(BaseModel):
    """리비전 응답 스키마."""

    id: str
    document_id: str
    source: str
    author_id: str
    summary: str
    parent_revision_id: Optional[str] = None
