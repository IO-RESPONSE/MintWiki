"""토론 댓글 추가(add comment) 동작 테스트."""
from datetime import datetime

from modules.discussion.comment import DiscussionComment
from modules.discussion.repository import InMemoryDiscussionRepository


class TestAddDiscussionComment:
    """저장소를 통한 토론 댓글 추가 테스트."""

    async def test_add_comment_persists_all_fields(self):
        """추가한 댓글의 모든 필드가 저장소에 그대로 저장된다."""
        repo = InMemoryDiscussionRepository()
        created_at = datetime(2026, 1, 1, 12, 0, 0)
        comment = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="동의합니다.",
            created_by="user1",
            created_at=created_at,
        )

        await repo.create_comment(comment)
        fetched = await repo.list_comments_by_thread_id("thread1")

        assert len(fetched) == 1
        assert fetched[0].id == "comment1"
        assert fetched[0].thread_id == "thread1"
        assert fetched[0].body == "동의합니다."
        assert fetched[0].created_by == "user1"
        assert fetched[0].created_at == created_at

    async def test_add_comment_returns_same_comment_instance(self):
        """create_comment는 저장한 댓글을 그대로 반환한다."""
        repo = InMemoryDiscussionRepository()
        comment = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="본문",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )

        result = await repo.create_comment(comment)

        assert result is comment

    async def test_added_comment_appears_in_thread_comment_list(self):
        """추가한 댓글은 해당 스레드의 댓글 목록에 포함된다."""
        repo = InMemoryDiscussionRepository()
        comment = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="본문",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )

        await repo.create_comment(comment)
        comments = await repo.list_comments_by_thread_id("thread1")

        assert len(comments) == 1
        assert comments[0] is comment

    async def test_adding_second_comment_does_not_overwrite_first(self):
        """서로 다른 id의 댓글을 추가해도 기존 댓글은 유지된다."""
        repo = InMemoryDiscussionRepository()
        comment1 = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="첫 번째 댓글",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        comment2 = DiscussionComment(
            id="comment2",
            thread_id="thread1",
            body="두 번째 댓글",
            created_by="user2",
            created_at=datetime(2026, 1, 2),
        )

        await repo.create_comment(comment1)
        await repo.create_comment(comment2)

        comments = await repo.list_comments_by_thread_id("thread1")
        assert len(comments) == 2
        assert comments[0] is comment1
        assert comments[1] is comment2

    async def test_comments_for_different_threads_do_not_mix(self):
        """서로 다른 스레드에 추가한 댓글은 섞이지 않는다."""
        repo = InMemoryDiscussionRepository()
        comment_thread1 = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="thread1 댓글",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        comment_thread2 = DiscussionComment(
            id="comment2",
            thread_id="thread2",
            body="thread2 댓글",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )

        await repo.create_comment(comment_thread1)
        await repo.create_comment(comment_thread2)

        thread1_comments = await repo.list_comments_by_thread_id("thread1")
        thread2_comments = await repo.list_comments_by_thread_id("thread2")
        assert len(thread1_comments) == 1
        assert len(thread2_comments) == 1
        assert thread1_comments[0].id == "comment1"
        assert thread2_comments[0].id == "comment2"
