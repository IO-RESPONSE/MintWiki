"""토론 스레드 상태 열거형 테스트."""
from modules.discussion.state import ThreadState


class TestThreadState:
    """ThreadState 열거형 값 테스트."""

    def test_has_open_member(self):
        """OPEN 멤버는 스레드의 open 문자열 값과 일치한다."""
        assert ThreadState.OPEN.value == "open"

    def test_has_closed_member(self):
        """CLOSED 멤버는 스레드의 closed 문자열 값과 일치한다."""
        assert ThreadState.CLOSED.value == "closed"

    def test_has_paused_member(self):
        """PAUSED 멤버는 스레드의 paused 문자열 값과 일치한다."""
        assert ThreadState.PAUSED.value == "paused"

    def test_members_are_distinct(self):
        """OPEN, CLOSED, PAUSED는 서로 다른 멤버다."""
        assert ThreadState.OPEN != ThreadState.CLOSED
        assert ThreadState.OPEN != ThreadState.PAUSED
        assert ThreadState.CLOSED != ThreadState.PAUSED
