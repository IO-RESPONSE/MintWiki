"""토론 스레드 모델 테스트."""
from datetime import datetime

import pytest
from modules.discussion.thread import (
    DiscussionThread,
    EmptyThreadCreatedByError,
    EmptyThreadDocumentIdError,
    EmptyThreadIdError,
    EmptyThreadTitleError,
)


class TestDiscussionThreadConstruction:
    """스레드 생성 테스트."""

    def test_creates_thread_with_required_fields(self):
        """필수 필드로 스레드를 생성한다."""
        created_at = datetime(2026, 1, 1, 0, 0, 0)
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목에 대한 이견",
            created_by="user1",
            created_at=created_at,
        )
        assert thread.id == "thread1"
        assert thread.document_id == "doc1"
        assert thread.title == "제목에 대한 이견"
        assert thread.created_by == "user1"
        assert thread.created_at == created_at
        assert thread.status == "open"
        assert thread.closed_at is None

    def test_creates_thread_with_explicit_status(self):
        """명시적인 상태로 스레드를 생성한다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
            status="closed",
        )
        assert thread.status == "closed"

    def test_rejects_empty_thread_id(self):
        """빈 스레드 id로 생성할 수 없다."""
        with pytest.raises(EmptyThreadIdError):
            DiscussionThread(
                id="",
                document_id="doc1",
                title="제목",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_whitespace_only_thread_id(self):
        """공백만 있는 스레드 id로 생성할 수 없다."""
        with pytest.raises(EmptyThreadIdError):
            DiscussionThread(
                id="   ",
                document_id="doc1",
                title="제목",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_empty_document_id(self):
        """빈 문서 id로 생성할 수 없다."""
        with pytest.raises(EmptyThreadDocumentIdError):
            DiscussionThread(
                id="thread1",
                document_id="",
                title="제목",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_empty_title(self):
        """빈 제목으로 생성할 수 없다."""
        with pytest.raises(EmptyThreadTitleError):
            DiscussionThread(
                id="thread1",
                document_id="doc1",
                title="",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_whitespace_only_title(self):
        """공백만 있는 제목으로 생성할 수 없다."""
        with pytest.raises(EmptyThreadTitleError):
            DiscussionThread(
                id="thread1",
                document_id="doc1",
                title="   ",
                created_by="user1",
                created_at=datetime(2026, 1, 1),
            )

    def test_rejects_empty_created_by(self):
        """빈 작성자 id로 생성할 수 없다."""
        with pytest.raises(EmptyThreadCreatedByError):
            DiscussionThread(
                id="thread1",
                document_id="doc1",
                title="제목",
                created_by="",
                created_at=datetime(2026, 1, 1),
            )


class TestDiscussionThreadState:
    """스레드 상태 전이 테스트."""

    def test_is_open_true_for_new_thread(self):
        """새로 생성된 스레드는 열려 있다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        assert thread.is_open() is True

    def test_close_marks_thread_closed(self):
        """close 호출 시 스레드가 닫힌 상태로 전환된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        closed_at = datetime(2026, 1, 2)
        thread.close(closed_at)
        assert thread.status == "closed"
        assert thread.closed_at == closed_at
        assert thread.is_open() is False

    def test_reopen_marks_thread_open(self):
        """reopen 호출 시 스레드가 열린 상태로 전환된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        thread.close(datetime(2026, 1, 2))

        thread.reopen()

        assert thread.status == "open"
        assert thread.closed_at is None
        assert thread.is_open() is True

    def test_pause_marks_thread_paused(self):
        """pause 호출 시 스레드가 일시정지 상태로 전환된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        paused_at = datetime(2026, 1, 2)
        thread.pause(paused_at)
        assert thread.status == "paused"
        assert thread.paused_at == paused_at
        assert thread.is_open() is False
        assert thread.is_paused() is True

    def test_is_paused_false_for_new_thread(self):
        """새로 생성된 스레드는 일시정지 상태가 아니다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        assert thread.is_paused() is False

    def test_reopen_from_paused_marks_thread_open(self):
        """일시정지된 스레드를 reopen하면 열린 상태로 전환된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        thread.pause(datetime(2026, 1, 2))

        thread.reopen()

        assert thread.status == "open"
        assert thread.is_open() is True
        assert thread.is_paused() is False
        assert thread.closed_at is None

    def test_close_from_paused_marks_thread_closed(self):
        """일시정지된 스레드를 close하면 닫힌 상태로 전환된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        thread.pause(datetime(2026, 1, 2))
        closed_at = datetime(2026, 1, 3)

        thread.close(closed_at)

        assert thread.status == "closed"
        assert thread.closed_at == closed_at
        assert thread.is_open() is False
        assert thread.is_paused() is False

    def test_pause_from_closed_marks_thread_paused(self):
        """닫힌 스레드를 pause하면 일시정지 상태로 전환된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        thread.close(datetime(2026, 1, 2))
        paused_at = datetime(2026, 1, 3)

        thread.pause(paused_at)

        assert thread.status == "paused"
        assert thread.paused_at == paused_at
        assert thread.is_open() is False
        assert thread.is_paused() is True

    def test_close_is_idempotent_and_updates_closed_at(self):
        """close를 두 번 호출해도 상태는 closed로 유지되고 시각은 갱신된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        thread.close(datetime(2026, 1, 2))
        second_closed_at = datetime(2026, 1, 3)

        thread.close(second_closed_at)

        assert thread.status == "closed"
        assert thread.closed_at == second_closed_at

    def test_pause_is_idempotent_and_updates_paused_at(self):
        """pause를 두 번 호출해도 상태는 paused로 유지되고 시각은 갱신된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        thread.pause(datetime(2026, 1, 2))
        second_paused_at = datetime(2026, 1, 3)

        thread.pause(second_paused_at)

        assert thread.status == "paused"
        assert thread.paused_at == second_paused_at

    def test_full_state_cycle_through_all_transitions(self):
        """open -> paused -> closed -> open 순환 전이에서 매 단계 상태가 일관된다."""
        thread = DiscussionThread(
            id="thread1",
            document_id="doc1",
            title="제목",
            created_by="user1",
            created_at=datetime(2026, 1, 1),
        )
        assert thread.is_open() is True

        thread.pause(datetime(2026, 1, 2))
        assert thread.is_paused() is True
        assert thread.is_open() is False

        thread.close(datetime(2026, 1, 3))
        assert thread.status == "closed"
        assert thread.is_open() is False
        assert thread.is_paused() is False

        thread.reopen()
        assert thread.status == "open"
        assert thread.is_open() is True
        assert thread.is_paused() is False
        assert thread.closed_at is None
