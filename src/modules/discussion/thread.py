"""토론 스레드 도메인 모델."""
from datetime import datetime
from typing import Optional


class EmptyThreadIdError(Exception):
    """스레드 id가 비어있을 때 발생."""

    pass


class EmptyThreadDocumentIdError(Exception):
    """스레드가 속한 문서 id가 비어있을 때 발생."""

    pass


class EmptyThreadTitleError(Exception):
    """스레드 제목이 비어있을 때 발생."""

    pass


class EmptyThreadCreatedByError(Exception):
    """스레드 작성자 id가 비어있을 때 발생."""

    pass


class DiscussionThread:
    """
    문서에 대한 토론 스레드를 나타내는 도메인 모델.

    스레드는 특정 문서를 주제로 열리며, 댓글과 상태(state)를 가진다.
    댓글 모델과 상태 열거형은 후속 태스크에서 추가되므로, 이 모델은
    상태를 단순 문자열("open"/"closed")로만 표현한다.
    """

    def __init__(
        self,
        id: str,
        document_id: str,
        title: str,
        created_by: str,
        created_at: datetime,
        status: str = "open",
        closed_at: Optional[datetime] = None,
    ):
        """
        토론 스레드를 생성한다.

        Args:
            id: 스레드의 고유 식별자
            document_id: 스레드가 속한 문서의 id
            title: 스레드 제목
            created_by: 스레드를 생성한 사용자의 id
            created_at: 스레드가 생성된 시각
            status: 스레드 상태 (기본값 "open")
            closed_at: 스레드가 닫힌 시각 (선택사항, 닫히지 않았으면 None)

        Raises:
            EmptyThreadIdError: 스레드 id가 비어있거나 공백만 있는 경우
            EmptyThreadDocumentIdError: 문서 id가 비어있거나 공백만 있는 경우
            EmptyThreadTitleError: 제목이 비어있거나 공백만 있는 경우
            EmptyThreadCreatedByError: 작성자 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyThreadIdError("스레드 id는 비어있을 수 없습니다")
        if not document_id or not document_id.strip():
            raise EmptyThreadDocumentIdError("문서 id는 비어있을 수 없습니다")
        if not title or not title.strip():
            raise EmptyThreadTitleError("스레드 제목은 비어있을 수 없습니다")
        if not created_by or not created_by.strip():
            raise EmptyThreadCreatedByError("작성자 id는 비어있을 수 없습니다")

        self.id = id
        self.document_id = document_id
        self.title = title
        self.created_by = created_by
        self.created_at = created_at
        self.status = status
        self.closed_at = closed_at

    def is_open(self) -> bool:
        """스레드가 열려 있는지 확인한다."""
        return self.status == "open"

    def close(self, now: datetime) -> None:
        """스레드를 닫는다."""
        self.status = "closed"
        self.closed_at = now

    def reopen(self) -> None:
        """스레드를 다시 연다."""
        self.status = "open"
        self.closed_at = None
