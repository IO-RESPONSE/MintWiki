"""토론 API 스키마."""
from pydantic import BaseModel


class CreateThreadRequest(BaseModel):
    """스레드 생성 요청 스키마."""

    document_id: str
    title: str
    created_by: str


class ThreadResponse(BaseModel):
    """스레드 응답 스키마."""

    id: str
    document_id: str
    title: str
    created_by: str
    status: str


class AddCommentRequest(BaseModel):
    """댓글 추가 요청 스키마."""

    body: str
    created_by: str


class CommentResponse(BaseModel):
    """댓글 응답 스키마."""

    id: str
    thread_id: str
    body: str
    created_by: str
    is_hidden: bool
