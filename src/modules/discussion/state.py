"""토론 스레드 상태를 나타내는 열거형."""
from enum import Enum


class ThreadState(Enum):
    """
    토론 스레드가 가질 수 있는 상태.

    DiscussionThread.status 필드에서 사용하는 문자열 값과 동일한 값을 가진다.
    """

    OPEN = "open"
    CLOSED = "closed"
    PAUSED = "paused"
