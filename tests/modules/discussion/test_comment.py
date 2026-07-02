"""토론 댓글 모델 테스트."""
from datetime import datetime

import pytest
from modules.discussion.comment import (
    DiscussionComment,
    EmptyCommentBodyError,
    EmptyCommentCreatedByError,
    EmptyCommentIdError,
    EmptyCommentThreadIdError,
)


class TestDiscussionCommentConstruction:
    """댓글 생성 테스트."""

    def test_creates_comment_with_required_fields(self):
        """필수 필드로 댓글을 생성한다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        comment = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="동의합니다.",
            created_by="user1",
            created_at=created_at,
        )
        assert comment.id == "comment1"
        assert comment.thread_id == "thread1"
        assert comment.body == "동의합니다."
        assert comment.created_by == "user1"
        assert comment.created_at == created_at

    def test_rejects_empty_comment_id(self):
        """빈 댓글 id로 생성할 수 없다."""
        with pytest.raises(EmptyCommentIdError):
            DiscussionComment(
                id="",
                thread_id="thread1",
                body="본문",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_whitespace_only_comment_id(self):
        """공백만 있는 댓글 id로 생성할 수 없다."""
        with pytest.raises(EmptyCommentIdError):
            DiscussionComment(
                id="   ",
                thread_id="thread1",
                body="본문",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_empty_thread_id(self):
        """빈 스레드 id로 생성할 수 없다."""
        with pytest.raises(EmptyCommentThreadIdError):
            DiscussionComment(
                id="comment1",
                thread_id="",
                body="본문",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_empty_body(self):
        """빈 본문으로 생성할 수 없다."""
        with pytest.raises(EmptyCommentBodyError):
            DiscussionComment(
                id="comment1",
                thread_id="thread1",
                body="",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_whitespace_only_body(self):
        """공백만 있는 본문으로 생성할 수 없다."""
        with pytest.raises(EmptyCommentBodyError):
            DiscussionComment(
                id="comment1",
                thread_id="thread1",
                body="   ",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_empty_created_by(self):
        """빈 작성자 id로 생성할 수 없다."""
        with pytest.raises(EmptyCommentCreatedByError):
            DiscussionComment(
                id="comment1",
                thread_id="thread1",
                body="본문",
                created_by="",
                created_at=datetime(2026, 1, 1),
            )

    def test_defaults_to_not_hidden(self):
        """기본적으로 댓글은 숨김 상태가 아니다."""
        comment = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="본문",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        assert comment.is_hidden is False
        assert comment.hidden_at is None

    def test_creates_hidden_comment_with_explicit_fields(self):
        """is_hidden과 hidden_at을 명시하여 댓글을 생성할 수 있다."""
        hidden_at = datetime(2026, 1, 2, 0, 0, 0)
        comment = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="본문",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
            is_hidden=True,
            hidden_at=hidden_at,
        )
        assert comment.is_hidden is True
        assert comment.hidden_at == hidden_at


class TestDiscussionCommentHide:
    """댓글 숨김 처리 테스트."""

    def test_hide_marks_comment_as_hidden(self):
        """hide 호출 시 댓글이 숨김 상태가 된다."""
        comment = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="본문",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )

        comment.hide(datetime(2026, 1, 2, 0, 0, 0))

        assert comment.is_hidden is True
        assert comment.hidden_at == datetime(2026, 1, 2, 0, 0, 0)
