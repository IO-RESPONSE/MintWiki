"""토론 댓글 도메인 모델."""
from datetime import datetime
from typing import Optional


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
        is_hidden: bool = False,
        hidden_at: Optional[datetime] = None,
    ):
        """
        토론 댓글을 생성한다.

        Args:
            id: 댓글의 고유 식별자
            thread_id: 댓글이 속한 스레드의 id
            body: 댓글 본문
            created_by: 댓글을 작성한 사용자의 id
            created_at: 댓글이 생성된 시각
            is_hidden: 댓글이 숨김 처리되었는지 여부 (기본값 False)
            hidden_at: 댓글이 숨겨진 시각 (선택사항, 숨겨지지 않았으면 None)

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
        self.is_hidden = is_hidden
        self.hidden_at = hidden_at

    def hide(self, now: datetime) -> None:
        """댓글을 숨김 처리한다."""
        self.is_hidden = True
        self.hidden_at = now

    def to_public_view(self) -> dict:
        """
        일반 사용자에게 노출할 댓글 뷰를 만든다.

        숨김 처리된 댓글은 모더레이터가 아닌 일반 사용자에게 본문을
        노출하지 않아야 하므로, is_hidden이 True이면 body를 None으로
        가린다. 모더레이터용 전체 뷰는 to_moderator_view에서 제공한다.

        Returns:
            일반 사용자에게 노출할 필드로 구성된 댓글 뷰 딕셔너리
        """
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "body": None if self.is_hidden else self.body,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "is_hidden": self.is_hidden,
            "hidden_at": self.hidden_at,
        }

    def to_moderator_view(self) -> dict:
        """
        모더레이터에게 노출할 댓글 뷰를 만든다.

        숨김 처리 여부와 무관하게 본문을 그대로 노출한다.

        Returns:
            모더레이터에게 노출할 필드로 구성된 댓글 뷰 딕셔너리
        """
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "body": self.body,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "is_hidden": self.is_hidden,
            "hidden_at": self.hidden_at,
        }
