"""토론 댓글 도메인 모델."""
from datetime import datetime


class EmptyCommentIdError(Exception):
    """댓글 id가 비어있을 때 발생."""

    pass


class EmptyCommentThreadIdError(Exception):
    """댓글이 속한 스레드 id가 비어있을 때 발생."""

    pass


class EmptyCommentBodyError(Exception):
    """댓글 본문이 비어있을 때 발생."""

    pass


class EmptyCommentCreatedByError(Exception):
    """댓글 작성자 id가 비어있을 때 발생."""

    pass


class DiscussionComment:
    """
    토론 스레드에 달린 댓글을 나타내는 도메인 모델.

    댓글은 특정 스레드에 속하며, 작성자와 본문을 가진다.
    """

    def __init__(
        self,
        id: str,
        thread_id: str,
        body: str,
        created_by: str,
        created_at: datetime,
    ):
        """
        토론 댓글을 생성한다.

        Args:
            id: 댓글의 고유 식별자
            thread_id: 댓글이 속한 스레드의 id
            body: 댓글 본문
            created_by: 댓글을 작성한 사용자의 id
            created_at: 댓글이 생성된 시각

        Raises:
            EmptyCommentIdError: 댓글 id가 비어있거나 공백만 있는 경우
            EmptyCommentThreadIdError: 스레드 id가 비어있거나 공백만 있는 경우
            EmptyCommentBodyError: 본문이 비어있거나 공백만 있는 경우
            EmptyCommentCreatedByError: 작성자 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyCommentIdError("댓글 id는 비어있을 수 없습니다")
        if not thread_id or not thread_id.strip():
            raise EmptyCommentThreadIdError("스레드 id는 비어있을 수 없습니다")
        if not body or not body.strip():
            raise EmptyCommentBodyError("댓글 본문은 비어있을 수 없습니다")
        if not created_by or not created_by.strip():
            raise EmptyCommentCreatedByError("작성자 id는 비어있을 수 없습니다")

        self.id = id
        self.thread_id = thread_id
        self.body = body
        self.created_by = created_by
        self.created_at = created_at
