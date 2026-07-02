"""토론 스레드 및 댓글 생성/조회 서비스."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from modules.discussion.audit_recorder import DiscussionAuditRecorder
from modules.discussion.comment import DiscussionComment
from modules.discussion.repository import (
    DiscussionCommentNotFoundError,
    DiscussionRepository,
    DiscussionThreadNotFoundError,
)
from modules.discussion.thread import DiscussionThread


class DiscussionService:
    """
    토론 스레드 및 댓글 생성과 조회를 담당하는 서비스.

    스레드/댓글 생성 시 id와 생성 시각을 부여하고 저장소에 위임한다.
    스레드 생성과 댓글 숨김 시에는 audit_recorder를 통해 감사 이벤트도
    함께 남긴다.
    """

    def __init__(
        self,
        repository: DiscussionRepository,
        audit_recorder: Optional[DiscussionAuditRecorder] = None,
    ):
        """
        서비스를 초기화한다.

        Args:
            repository: 토론 저장소
            audit_recorder: 감사 이벤트 기록기 (선택사항, 생략하면 새로
                생성한다)
        """
        self.repository = repository
        self.audit_recorder = audit_recorder or DiscussionAuditRecorder()

    async def create_thread(
        self, document_id: str, title: str, created_by: str
    ) -> DiscussionThread:
        """
        새로운 토론 스레드를 생성한다.

        Args:
            document_id: 스레드가 속할 문서의 id
            title: 스레드 제목
            created_by: 스레드를 생성하는 사용자의 id

        Returns:
            생성된 토론 스레드
        """
        thread = DiscussionThread(
            id=str(uuid.uuid4()),
            document_id=document_id,
            title=title,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )
        created = await self.repository.create_thread(thread)
        self.audit_recorder.record_thread_created(created, actor_id=created_by)
        return created

    async def get_thread(self, id: str) -> Optional[DiscussionThread]:
        """
        주어진 id로 토론 스레드를 조회한다.

        Args:
            id: 조회할 토론 스레드의 고유 식별자

        Returns:
            조회된 토론 스레드 또는 없으면 None
        """
        return await self.repository.get_thread(id)

    async def list_threads_by_document_id(
        self, document_id: str, limit: Optional[int] = None, offset: int = 0
    ) -> list[DiscussionThread]:
        """
        주어진 문서의 토론 스레드를 생성 순서대로 나열한다.

        Args:
            document_id: 조회할 문서의 고유 식별자
            limit: 반환할 최대 개수 (선택사항, 생략하면 제한 없음)
            offset: 건너뛸 개수 (기본값 0)

        Returns:
            문서의 토론 스레드 목록 (생성 순서, limit/offset 적용됨)
        """
        return await self.repository.list_threads_by_document_id(
            document_id, limit=limit, offset=offset
        )

    async def close_thread(self, thread_id: str) -> DiscussionThread:
        """
        토론 스레드를 닫는다.

        Args:
            thread_id: 닫을 스레드의 id

        Returns:
            닫힌 토론 스레드

        Raises:
            DiscussionThreadNotFoundError: 스레드가 없는 경우
        """
        thread = await self.repository.get_thread(thread_id)
        if thread is None:
            raise DiscussionThreadNotFoundError(f"스레드 id '{thread_id}'를 찾을 수 없습니다")
        thread.close(datetime.now(timezone.utc))
        return await self.repository.update_thread(thread)

    async def reopen_thread(self, thread_id: str) -> DiscussionThread:
        """
        닫힌 토론 스레드를 다시 연다.

        Args:
            thread_id: 다시 열 스레드의 id

        Returns:
            다시 열린 토론 스레드

        Raises:
            DiscussionThreadNotFoundError: 스레드가 없는 경우
        """
        thread = await self.repository.get_thread(thread_id)
        if thread is None:
            raise DiscussionThreadNotFoundError(f"스레드 id '{thread_id}'를 찾을 수 없습니다")
        thread.reopen()
        return await self.repository.update_thread(thread)

    async def pause_thread(self, thread_id: str) -> DiscussionThread:
        """
        토론 스레드를 일시정지한다.

        Args:
            thread_id: 일시정지할 스레드의 id

        Returns:
            일시정지된 토론 스레드

        Raises:
            DiscussionThreadNotFoundError: 스레드가 없는 경우
        """
        thread = await self.repository.get_thread(thread_id)
        if thread is None:
            raise DiscussionThreadNotFoundError(f"스레드 id '{thread_id}'를 찾을 수 없습니다")
        thread.pause(datetime.now(timezone.utc))
        return await self.repository.update_thread(thread)

    async def add_comment(
        self, thread_id: str, body: str, created_by: str
    ) -> DiscussionComment:
        """
        토론 스레드에 새로운 댓글을 추가한다.

        Args:
            thread_id: 댓글이 속할 스레드의 id
            body: 댓글 본문
            created_by: 댓글을 작성하는 사용자의 id

        Returns:
            생성된 댓글
        """
        comment = DiscussionComment(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            body=body,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )
        return await self.repository.create_comment(comment)

    async def list_comments_by_thread_id(
        self, thread_id: str, limit: Optional[int] = None, offset: int = 0
    ) -> list[DiscussionComment]:
        """
        주어진 스레드의 댓글을 생성 순서대로 나열한다.

        Args:
            thread_id: 조회할 스레드의 고유 식별자
            limit: 반환할 최대 개수 (선택사항, 생략하면 제한 없음)
            offset: 건너뛸 개수 (기본값 0)

        Returns:
            스레드의 댓글 목록 (생성 순서, limit/offset 적용됨)
        """
        return await self.repository.list_comments_by_thread_id(
            thread_id, limit=limit, offset=offset
        )

    async def hide_comment(
        self, comment_id: str, actor_id: Optional[str] = None
    ) -> DiscussionComment:
        """
        댓글을 숨김 처리하고 감사 이벤트를 남긴다.

        Args:
            comment_id: 숨길 댓글의 id
            actor_id: 댓글을 숨긴 사용자(주로 모더레이터)의 id (선택사항)

        Returns:
            숨김 처리된 댓글

        Raises:
            DiscussionCommentNotFoundError: 댓글이 없는 경우
        """
        comment = await self.repository.get_comment(comment_id)
        if comment is None:
            raise DiscussionCommentNotFoundError(f"댓글 id '{comment_id}'를 찾을 수 없습니다")
        comment.hide(datetime.now(timezone.utc))
        hidden = await self.repository.update_comment(comment)
        self.audit_recorder.record_comment_hidden(hidden, actor_id=actor_id)
        return hidden
