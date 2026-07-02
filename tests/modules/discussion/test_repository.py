"""토론 저장소 인터페이스 테스트."""
from datetime import datetime

import pytest

from modules.discussion.comment import DiscussionComment
from modules.discussion.repository import (
    DiscussionRepository,
    DiscussionThreadNotFoundError,
    InMemoryDiscussionRepository,
)
from modules.discussion.thread import DiscussionThread


class TestDiscussionRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            DiscussionRepository()

    def test_create_thread_method_exists(self):
        """저장소는 create_thread 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "create_thread")

    def test_get_thread_method_exists(self):
        """저장소는 get_thread 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "get_thread")

    def test_list_threads_by_document_id_method_exists(self):
        """저장소는 list_threads_by_document_id 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "list_threads_by_document_id")

    def test_update_thread_method_exists(self):
        """저장소는 update_thread 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "update_thread")

    def test_create_comment_method_exists(self):
        """저장소는 create_comment 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "create_comment")

    def test_list_comments_by_thread_id_method_exists(self):
        """저장소는 list_comments_by_thread_id 메서드를 정의한다."""
        assert hasattr(DiscussionRepository, "list_comments_by_thread_id")


class TestInMemoryDiscussionRepository:
    """인메모리 저장소 구현 테스트."""

    @pytest.mark.asyncio
    async def test_can_create_thread(self):
        """인메모리 저장소는 토론 스레드를 생성할 수 있다."""
        repo = InMemoryDiscussionRepository()
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목에 대한 이견",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        result = await repo.create_thread(thread)
        assert result.id == "thread1"
        assert result.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_can_get_thread_by_id(self):
        """인메모리 저장소는 id로 토론 스레드를 조회할 수 있다."""
        repo = InMemoryDiscussionRepository()
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        await repo.create_thread(thread)
        result = await repo.get_thread("thread1")
        assert result is not None
        assert result.id == "thread1"

    @pytest.mark.asyncio
    async def test_get_thread_returns_none_for_missing_id(self):
        """인메모리 저장소는 없는 id를 조회하면 None을 반환한다."""
        repo = InMemoryDiscussionRepository()
        result = await repo.get_thread("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_list_threads_by_document_id_in_creation_order(self):
        """인메모리 저장소는 문서의 스레드를 생성 순서대로 나열할 수 있다."""
        repo = InMemoryDiscussionRepository()
        thread1 = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="첫 번째 이견",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        thread2 = DiscussionThread(
            id="thread2",
            document_id="doc1",
            title="두 번째 이견",
            created_by="user2",
            created_at=datetime(2026, 1, 2, 0, 0, 0),
        )
        await repo.create_thread(thread1)
        await repo.create_thread(thread2)
        result = await repo.list_threads_by_document_id("doc1")
        assert len(result) == 2
        assert result[0].id == "thread1"
        assert result[1].id == "thread2"

    @pytest.mark.asyncio
    async def test_list_threads_returns_empty_list_for_missing_document(self):
        """인메모리 저장소는 없는 문서의 스레드를 조회하면 빈 목록을 반환한다."""
        repo = InMemoryDiscussionRepository()
        result = await repo.list_threads_by_document_id("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_can_update_thread(self):
        """인메모리 저장소는 토론 스레드를 업데이트할 수 있다."""
        repo = InMemoryDiscussionRepository()
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        await repo.create_thread(thread)
        thread.close(datetime(2026, 1, 2, 0, 0, 0))
        result = await repo.update_thread(thread)
        assert result.status == "closed"
        fetched = await repo.get_thread("thread1")
        assert fetched.status == "closed"

    @pytest.mark.asyncio
    async def test_update_thread_raises_for_missing_thread(self):
        """인메모리 저장소는 없는 스레드를 업데이트하면 예외를 발생시킨다."""
        repo = InMemoryDiscussionRepository()
        thread = DiscussionThread(
            id="nonexistent",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        with pytest.raises(DiscussionThreadNotFoundError):
            await repo.update_thread(thread)

    @pytest.mark.asyncio
    async def test_can_create_comment(self):
        """인메모리 저장소는 댓글을 생성할 수 있다."""
        repo = InMemoryDiscussionRepository()
        comment = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="댓글 내용",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        result = await repo.create_comment(comment)
        assert result.id == "comment1"
        assert result.thread_id == "thread1"

    @pytest.mark.asyncio
    async def test_can_list_comments_by_thread_id_in_creation_order(self):
        """인메모리 저장소는 스레드의 댓글을 생성 순서대로 나열할 수 있다."""
        repo = InMemoryDiscussionRepository()
        comment1 = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="첫 번째 댓글",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        comment2 = DiscussionComment(
            id="comment2",
            thread_id="thread1",
            body="두 번째 댓글",
            created_by="user2",
            created_at=datetime(2026, 1, 2, 0, 0, 0),
        )
        await repo.create_comment(comment1)
        await repo.create_comment(comment2)
        result = await repo.list_comments_by_thread_id("thread1")
        assert len(result) == 2
        assert result[0].id == "comment1"
        assert result[1].id == "comment2"

    @pytest.mark.asyncio
    async def test_list_comments_returns_empty_list_for_missing_thread(self):
        """인메모리 저장소는 없는 스레드의 댓글을 조회하면 빈 목록을 반환한다."""
        repo = InMemoryDiscussionRepository()
        result = await repo.list_comments_by_thread_id("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_can_store_threads_and_comments_for_different_documents(self):
        """인메모리 저장소는 여러 문서와 스레드의 데이터를 독립적으로 저장할 수 있다."""
        repo = InMemoryDiscussionRepository()
        thread_doc1 = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="doc1 이견",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        thread_doc2 = DiscussionThread(
            id="thread2",
            document_id="doc2",
            title="doc2 이견",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        await repo.create_thread(thread_doc1)
        await repo.create_thread(thread_doc2)

        doc1_threads = await repo.list_threads_by_document_id("doc1")
        doc2_threads = await repo.list_threads_by_document_id("doc2")
        assert len(doc1_threads) == 1
        assert len(doc2_threads) == 1
        assert doc1_threads[0].id == "thread1"
        assert doc2_threads[0].id == "thread2"

    @pytest.mark.asyncio
    async def test_list_threads_by_document_id_ignores_interleaved_other_documents(self):
        """인메모리 저장소는 다른 문서의 스레드가 섞여 생성되어도 대상 문서의 스레드만 생성 순서대로 나열한다."""
        repo = InMemoryDiscussionRepository()
        thread_doc1_a = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="doc1 첫 번째 이견",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        thread_doc2_a = DiscussionThread(
            id="thread2",
            document_id="doc2",
            title="doc2 첫 번째 이견",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        thread_doc1_b = DiscussionThread(
            id="thread3",
            document_id="doc1",
            title="doc1 두 번째 이견",
            created_by="user2",
            created_at=datetime(2026, 1, 2, 0, 0, 0),
        )
        await repo.create_thread(thread_doc1_a)
        await repo.create_thread(thread_doc2_a)
        await repo.create_thread(thread_doc1_b)

        doc1_threads = await repo.list_threads_by_document_id("doc1")
        assert [t.id for t in doc1_threads] == ["thread1", "thread3"]

    @pytest.mark.asyncio
    async def test_list_comments_by_thread_id_ignores_interleaved_other_threads(self):
        """인메모리 저장소는 다른 스레드의 댓글이 섞여 생성되어도 대상 스레드의 댓글만 생성 순서대로 나열한다."""
        repo = InMemoryDiscussionRepository()
        comment_thread1_a = DiscussionComment(
            id="comment1",
            thread_id="thread1",
            body="thread1 첫 번째 댓글",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        comment_thread2_a = DiscussionComment(
            id="comment2",
            thread_id="thread2",
            body="thread2 첫 번째 댓글",
            created_by="user1",
            created_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        comment_thread1_b = DiscussionComment(
            id="comment3",
            thread_id="thread1",
            body="thread1 두 번째 댓글",
            created_by="user2",
            created_at=datetime(2026, 1, 2, 0, 0, 0),
        )
        await repo.create_comment(comment_thread1_a)
        await repo.create_comment(comment_thread2_a)
        await repo.create_comment(comment_thread1_b)

        thread1_comments = await repo.list_comments_by_thread_id("thread1")
        assert [c.id for c in thread1_comments] == ["comment1", "comment3"]
