"""토론 스레드 및 댓글 생성/조회 서비스."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from modules.discussion.comment import DiscussionComment
from modules.discussion.repository import DiscussionRepository
from modules.discussion.thread import DiscussionThread


class DiscussionService:
    """
    토론 스레드 및 댓글 생성과 조회를 담당하는 서비스.

    스레드/댓글 생성 시 id와 생성 시각을 부여하고 저장소에 위임한다.
    스레드 상태 전환, 로그 기록 등의 세부 동작은 이후 태스크에서 채워지므로,
    이 서비스는 생성과 조회만 제공하는 골격이다.
    """

    def __init__(self, repository: DiscussionRepository):
        """
        서비스를 초기화한다.

        Args:
            repository: 토론 저장소
        """
        self.repository = repository

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
        return await self.repository.create_thread(thread)

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
        self, document_id: str
    ) -> list[DiscussionThread]:
        """
        주어진 문서의 토론 스레드를 생성 순서대로 나열한다.

        Args:
            document_id: 조회할 문서의 고유 식별자

        Returns:
            문서의 토론 스레드 목록 (생성 순서)
        """
        return await self.repository.list_threads_by_document_id(document_id)

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
        self, thread_id: str
    ) -> list[DiscussionComment]:
        """
        주어진 스레드의 댓글을 생성 순서대로 나열한다.

        Args:
            thread_id: 조회할 스레드의 고유 식별자

        Returns:
            스레드의 댓글 목록 (생성 순서)
        """
        return await self.repository.list_comments_by_thread_id(thread_id)
