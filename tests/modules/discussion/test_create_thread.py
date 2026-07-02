"""토론 스레드 생성(create thread) 동작 테스트."""
from datetime import datetime

from modules.discussion.repository import InMemoryDiscussionRepository
from modules.discussion.thread import DiscussionThread


class TestCreateDiscussionThread:
    """저장소를 통한 토론 스레드 생성 테스트."""

    async def test_create_thread_persists_all_fields(self):
        """생성한 스레드의 모든 필드가 저장소에 그대로 저장된다."""
        repo = InMemoryDiscussionRepository()
        created_at = datetime(2026, 1, 1, 12, 0, 0)
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목에 대한 이견",
            created_by="user1",
            created_at=created_at,
        )

        await repo.create_thread(thread)
        fetched = await repo.get_thread("thread1")

        assert fetched is not None
        assert fetched.id == "thread1"
        assert fetched.document_id == "doc1"
        assert fetched.title == "제목에 대한 이견"
        assert fetched.created_by == "user1"
        assert fetched.created_at == created_at
        assert fetched.status == "open"
        assert fetched.closed_at is None

    async def test_create_thread_returns_same_thread_instance(self):
        """create_thread는 저장한 스레드를 그대로 반환한다."""
        repo = InMemoryDiscussionRepository()
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )

        result = await repo.create_thread(thread)

        assert result is thread

    async def test_created_thread_appears_in_document_thread_list(self):
        """생성한 스레드는 해당 문서의 스레드 목록에 포함된다."""
        repo = InMemoryDiscussionRepository()
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )

        await repo.create_thread(thread)
        threads = await repo.list_threads_by_document_id("doc1")

        assert len(threads) == 1
        assert threads[0] is thread

    async def test_creating_second_thread_does_not_overwrite_first(self):
        """서로 다른 id의 스레드를 생성해도 기존 스레드는 유지된다."""
        repo = InMemoryDiscussionRepository()
        thread1 = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="첫 번째 이견",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        thread2 = DiscussionThread(
            id="thread2",
            document_id="doc1",
            title="두 번째 이견",
            created_by="user2",
            created_at=datetime(2026, 1, 2),
        )

        await repo.create_thread(thread1)
        await repo.create_thread(thread2)

        first = await repo.get_thread("thread1")
        second = await repo.get_thread("thread2")
        assert first is thread1
        assert second is thread2

    async def test_newly_created_thread_is_open_by_default(self):
        """생성 직후의 스레드는 열린 상태이다."""
        repo = InMemoryDiscussionRepository()
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )

        await repo.create_thread(thread)
        fetched = await repo.get_thread("thread1")

        assert fetched.is_open() is True
