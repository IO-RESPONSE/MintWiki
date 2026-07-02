"""토론 서비스 테스트."""
import pytest

from modules.discussion.comment import (
    EmptyCommentBodyError,
    EmptyCommentCreatedByError,
    EmptyCommentThreadIdError,
)
from modules.discussion.repository import (
    DiscussionThreadNotFoundError,
    InMemoryDiscussionRepository,
)
from modules.discussion.service import DiscussionService
from modules.discussion.thread import (
    EmptyThreadCreatedByError,
    EmptyThreadDocumentIdError,
    EmptyThreadTitleError,
)


class TestDiscussionServiceThreads:
    """토론 서비스의 스레드 생성/조회 테스트."""

    @pytest.mark.asyncio
    async def test_create_thread(self):
        """서비스는 토론 스레드를 생성할 수 있다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        thread = await service.create_thread(
            document_id="doc1",
            title="제목에 대한 이견",
            created_by="user1",
        )

        assert thread.id is not None
        assert thread.document_id == "doc1"
        assert thread.title == "제목에 대한 이견"
        assert thread.created_by == "user1"
        assert thread.is_open() is True

    @pytest.mark.asyncio
    async def test_create_generates_unique_ids(self):
        """서비스는 각 스레드에 고유한 id를 생성한다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        thread1 = await service.create_thread(
            document_id="doc1", title="첫 번째", created_by="user1"
        )
        thread2 = await service.create_thread(
            document_id="doc1", title="두 번째", created_by="user1"
        )

        assert thread1.id != thread2.id

    @pytest.mark.asyncio
    async def test_create_thread_delegates_to_repository(self):
        """서비스는 저장소에 스레드 생성을 위임한다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        retrieved = await repo.get_thread(thread.id)
        assert retrieved is not None
        assert retrieved.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_get_thread_by_id(self):
        """서비스는 id로 스레드를 조회할 수 있다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        created = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        retrieved = await service.get_thread(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_thread_returns_none(self):
        """서비스는 존재하지 않는 id를 조회하면 None을 반환한다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        result = await service.get_thread("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_threads_by_document_id(self):
        """서비스는 문서의 스레드를 생성 순서대로 나열할 수 있다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        thread1 = await service.create_thread(
            document_id="doc1", title="첫 번째", created_by="user1"
        )
        thread2 = await service.create_thread(
            document_id="doc1", title="두 번째", created_by="user2"
        )

        result = await service.list_threads_by_document_id("doc1")

        assert len(result) == 2
        assert result[0].id == thread1.id
        assert result[1].id == thread2.id

    @pytest.mark.asyncio
    async def test_list_threads_for_nonexistent_document(self):
        """서비스는 없는 문서의 스레드를 조회하면 빈 목록을 반환한다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        result = await service.list_threads_by_document_id("nonexistent")

        assert result == []

    @pytest.mark.asyncio
    async def test_create_thread_raises_on_empty_document_id(self):
        """서비스는 빈 문서 id로 생성하면 예외를 발생시킨다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        with pytest.raises(EmptyThreadDocumentIdError):
            await service.create_thread(document_id="", title="제목", created_by="user1")

    @pytest.mark.asyncio
    async def test_create_thread_raises_on_empty_title(self):
        """서비스는 빈 제목으로 생성하면 예외를 발생시킨다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        with pytest.raises(EmptyThreadTitleError):
            await service.create_thread(document_id="doc1", title="", created_by="user1")

    @pytest.mark.asyncio
    async def test_create_thread_raises_on_empty_created_by(self):
        """서비스는 빈 작성자 id로 생성하면 예외를 발생시킨다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        with pytest.raises(EmptyThreadCreatedByError):
            await service.create_thread(document_id="doc1", title="제목", created_by="")

    @pytest.mark.asyncio
    async def test_create_thread_does_not_persist_on_validation_error(self):
        """서비스는 검증에 실패한 스레드를 저장소에 남기지 않는다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        with pytest.raises(EmptyThreadTitleError):
            await service.create_thread(document_id="doc1", title="", created_by="user1")

        assert await service.list_threads_by_document_id("doc1") == []

    @pytest.mark.asyncio
    async def test_close_thread(self):
        """서비스는 열려 있는 스레드를 닫을 수 있다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        closed = await service.close_thread(thread.id)

        assert closed.id == thread.id
        assert closed.is_open() is False
        assert closed.closed_at is not None

    @pytest.mark.asyncio
    async def test_close_thread_delegates_to_repository(self):
        """서비스는 저장소에 스레드 닫기를 위임한다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        await service.close_thread(thread.id)

        retrieved = await repo.get_thread(thread.id)
        assert retrieved.is_open() is False

    @pytest.mark.asyncio
    async def test_close_nonexistent_thread_raises(self):
        """서비스는 존재하지 않는 스레드를 닫으려 하면 예외를 발생시킨다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        with pytest.raises(DiscussionThreadNotFoundError):
            await service.close_thread("nonexistent-id")


class TestDiscussionServiceComments:
    """토론 서비스의 댓글 추가/조회 테스트."""

    @pytest.mark.asyncio
    async def test_add_comment(self):
        """서비스는 스레드에 댓글을 추가할 수 있다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        comment = await service.add_comment(
            thread_id=thread.id, body="동의합니다.", created_by="user2"
        )

        assert comment.id is not None
        assert comment.thread_id == thread.id
        assert comment.body == "동의합니다."
        assert comment.created_by == "user2"

    @pytest.mark.asyncio
    async def test_add_comment_generates_unique_ids(self):
        """서비스는 각 댓글에 고유한 id를 생성한다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        comment1 = await service.add_comment(
            thread_id=thread.id, body="첫 번째", created_by="user1"
        )
        comment2 = await service.add_comment(
            thread_id=thread.id, body="두 번째", created_by="user2"
        )

        assert comment1.id != comment2.id

    @pytest.mark.asyncio
    async def test_add_comment_delegates_to_repository(self):
        """서비스는 저장소에 댓글 생성을 위임한다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        comment = await service.add_comment(
            thread_id=thread.id, body="본문", created_by="user1"
        )

        retrieved = await repo.list_comments_by_thread_id(thread.id)
        assert len(retrieved) == 1
        assert retrieved[0].id == comment.id

    @pytest.mark.asyncio
    async def test_list_comments_by_thread_id(self):
        """서비스는 스레드의 댓글을 생성 순서대로 나열할 수 있다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        comment1 = await service.add_comment(
            thread_id=thread.id, body="첫 번째", created_by="user1"
        )
        comment2 = await service.add_comment(
            thread_id=thread.id, body="두 번째", created_by="user2"
        )

        result = await service.list_comments_by_thread_id(thread.id)

        assert len(result) == 2
        assert result[0].id == comment1.id
        assert result[1].id == comment2.id

    @pytest.mark.asyncio
    async def test_list_comments_for_nonexistent_thread(self):
        """서비스는 없는 스레드의 댓글을 조회하면 빈 목록을 반환한다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        result = await service.list_comments_by_thread_id("nonexistent")

        assert result == []

    @pytest.mark.asyncio
    async def test_add_comment_raises_on_empty_thread_id(self):
        """서비스는 빈 스레드 id로 댓글을 추가하면 예외를 발생시킨다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)

        with pytest.raises(EmptyCommentThreadIdError):
            await service.add_comment(thread_id="", body="본문", created_by="user1")

    @pytest.mark.asyncio
    async def test_add_comment_raises_on_empty_body(self):
        """서비스는 빈 본문으로 댓글을 추가하면 예외를 발생시킨다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        with pytest.raises(EmptyCommentBodyError):
            await service.add_comment(thread_id=thread.id, body="", created_by="user1")

    @pytest.mark.asyncio
    async def test_add_comment_raises_on_empty_created_by(self):
        """서비스는 빈 작성자 id로 댓글을 추가하면 예외를 발생시킨다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        with pytest.raises(EmptyCommentCreatedByError):
            await service.add_comment(thread_id=thread.id, body="본문", created_by="")

    @pytest.mark.asyncio
    async def test_add_comment_does_not_persist_on_validation_error(self):
        """서비스는 검증에 실패한 댓글을 저장소에 남기지 않는다."""
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )

        with pytest.raises(EmptyCommentBodyError):
            await service.add_comment(thread_id=thread.id, body="", created_by="user1")

        assert await service.list_comments_by_thread_id(thread.id) == []
