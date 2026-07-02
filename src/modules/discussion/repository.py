"""토론 저장소 인터페이스 및 구현."""
from abc import ABC, abstractmethod
from typing import Optional

from modules.discussion.comment import DiscussionComment
from modules.discussion.thread import DiscussionThread


class DiscussionThreadNotFoundError(Exception):
    """토론 스레드를 찾을 수 없을 때 발생."""

    pass


class DiscussionCommentNotFoundError(Exception):
    """토론 댓글을 찾을 수 없을 때 발생."""

    pass


class DiscussionRepository(ABC):
    """
    토론 저장소의 인터페이스.

    저장소는 토론 스레드와 댓글을 저장하고 검색하는 메서드를 정의한다.
    구체적인 저장소 구현(메모리, 데이터베이스 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def create_thread(self, thread: DiscussionThread) -> DiscussionThread:
        """
        새로운 토론 스레드를 저장소에 저장한다.

        Args:
            thread: 저장할 토론 스레드

        Returns:
            저장된 토론 스레드

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
    async def get_thread(self, id: str) -> Optional[DiscussionThread]:
        """
        주어진 id로 토론 스레드를 조회한다.

        Args:
            id: 조회할 토론 스레드의 고유 식별자

        Returns:
            조회된 토론 스레드 또는 없으면 None
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def update_thread(self, thread: DiscussionThread) -> DiscussionThread:
        """
        기존 토론 스레드를 업데이트한다.

        Args:
            thread: 업데이트할 토론 스레드

        Returns:
            업데이트된 토론 스레드

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
    async def create_comment(self, comment: DiscussionComment) -> DiscussionComment:
        """
        새로운 댓글을 저장소에 저장한다.

        Args:
            comment: 저장할 댓글

        Returns:
            저장된 댓글

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_comment(self, id: str) -> Optional[DiscussionComment]:
        """
        주어진 id로 댓글을 조회한다.

        Args:
            id: 조회할 댓글의 고유 식별자

        Returns:
            조회된 댓글 또는 없으면 None
        """
        pass

    @abstractmethod
    async def update_comment(self, comment: DiscussionComment) -> DiscussionComment:
        """
        기존 댓글을 업데이트한다.

        Args:
            comment: 업데이트할 댓글

        Returns:
            업데이트된 댓글

        Raises:
            DiscussionCommentNotFoundError: 댓글이 없는 경우
        """
        pass


class InMemoryDiscussionRepository(DiscussionRepository):
    """
    메모리에 토론 스레드와 댓글을 저장하는 저장소 구현.

    초기 테스트 및 개발 단계에서 사용하기 위한 메모리 기반
    저장소 구현이다.
    """

    def __init__(self):
        """저장소를 초기화한다."""
        self.threads: dict[str, DiscussionThread] = {}
        self.document_threads: dict[str, list[str]] = {}
        self.comments: dict[str, DiscussionComment] = {}
        self.thread_comments: dict[str, list[str]] = {}

    async def create_thread(self, thread: DiscussionThread) -> DiscussionThread:
        """
        새로운 토론 스레드를 저장소에 저장한다.

        Args:
            thread: 저장할 토론 스레드

        Returns:
            저장된 토론 스레드
        """
        self.threads[thread.id] = thread
        self.document_threads.setdefault(thread.document_id, []).append(thread.id)
        return thread

    async def get_thread(self, id: str) -> Optional[DiscussionThread]:
        """
        주어진 id로 토론 스레드를 조회한다.

        Args:
            id: 조회할 토론 스레드의 고유 식별자

        Returns:
            조회된 토론 스레드 또는 없으면 None
        """
        return self.threads.get(id)

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
        thread_ids = self.document_threads.get(document_id, [])
        sliced_ids = thread_ids[offset:] if limit is None else thread_ids[offset : offset + limit]
        return [self.threads[tid] for tid in sliced_ids]

    async def update_thread(self, thread: DiscussionThread) -> DiscussionThread:
        """
        기존 토론 스레드를 업데이트한다.

        Args:
            thread: 업데이트할 토론 스레드

        Returns:
            업데이트된 토론 스레드

        Raises:
            DiscussionThreadNotFoundError: 스레드가 없는 경우
        """
        if thread.id not in self.threads:
            raise DiscussionThreadNotFoundError(f"스레드 id '{thread.id}'를 찾을 수 없습니다")
        self.threads[thread.id] = thread
        return thread

    async def create_comment(self, comment: DiscussionComment) -> DiscussionComment:
        """
        새로운 댓글을 저장소에 저장한다.

        Args:
            comment: 저장할 댓글

        Returns:
            저장된 댓글
        """
        self.comments[comment.id] = comment
        self.thread_comments.setdefault(comment.thread_id, []).append(comment.id)
        return comment

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
        comment_ids = self.thread_comments.get(thread_id, [])
        sliced_ids = (
            comment_ids[offset:] if limit is None else comment_ids[offset : offset + limit]
        )
        return [self.comments[cid] for cid in sliced_ids]

    async def get_comment(self, id: str) -> Optional[DiscussionComment]:
        """
        주어진 id로 댓글을 조회한다.

        Args:
            id: 조회할 댓글의 고유 식별자

        Returns:
            조회된 댓글 또는 없으면 None
        """
        return self.comments.get(id)

    async def update_comment(self, comment: DiscussionComment) -> DiscussionComment:
        """
        기존 댓글을 업데이트한다.

        Args:
            comment: 업데이트할 댓글

        Returns:
            업데이트된 댓글

        Raises:
            DiscussionCommentNotFoundError: 댓글이 없는 경우
        """
        if comment.id not in self.comments:
            raise DiscussionCommentNotFoundError(f"댓글 id '{comment.id}'를 찾을 수 없습니다")
        self.comments[comment.id] = comment
        return comment
