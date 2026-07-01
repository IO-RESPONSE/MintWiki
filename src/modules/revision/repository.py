"""리비전 저장소 인터페이스 및 구현."""
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.revision.model import Revision
from persistence.models import RevisionORM


class RevisionRepository(ABC):
    """
    리비전 저장소의 인터페이스.

    저장소는 리비전을 저장하고 검색하는 메서드를 정의한다.
    구체적인 저장소 구현(메모리, 데이터베이스 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def create(self, revision: Revision) -> Revision:
        """
        새로운 리비전을 저장소에 저장한다.

        Args:
            revision: 저장할 리비전

        Returns:
            저장된 리비전

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Revision]:
        """
        주어진 id로 리비전을 조회한다.

        Args:
            id: 조회할 리비전의 고유 식별자

        Returns:
            조회된 리비전 또는 없으면 None
        """
        pass

    @abstractmethod
    async def list_by_document_id(self, document_id: str) -> list[Revision]:
        """
        주어진 문서의 리비전을 생성 순서대로 나열한다.

        Args:
            document_id: 조회할 문서의 고유 식별자

        Returns:
            문서의 리비전 목록 (생성 순서)
        """
        pass


class InMemoryRevisionRepository(RevisionRepository):
    """
    메모리에 리비전을 저장하는 저장소 구현.

    초기 테스트 및 개발 단계에서 사용하기 위한 메모리 기반
    저장소 구현이다.
    """

    def __init__(self):
        """저장소를 초기화한다."""
        self.revisions: dict[str, Revision] = {}
        self.document_revisions: dict[str, list[str]] = {}

    async def create(self, revision: Revision) -> Revision:
        """
        새로운 리비전을 저장소에 저장한다.

        Args:
            revision: 저장할 리비전

        Returns:
            저장된 리비전
        """
        self.revisions[revision.id] = revision
        if revision.document_id not in self.document_revisions:
            self.document_revisions[revision.document_id] = []
        self.document_revisions[revision.document_id].append(revision.id)
        return revision

    async def get(self, id: str) -> Optional[Revision]:
        """
        주어진 id로 리비전을 조회한다.

        Args:
            id: 조회할 리비전의 고유 식별자

        Returns:
            조회된 리비전 또는 없으면 None
        """
        return self.revisions.get(id)

    async def list_by_document_id(self, document_id: str) -> list[Revision]:
        """
        주어진 문서의 리비전을 생성 순서대로 나열한다.

        Args:
            document_id: 조회할 문서의 고유 식별자

        Returns:
            문서의 리비전 목록 (생성 순서)
        """
        revision_ids = self.document_revisions.get(document_id, [])
        return [self.revisions[rid] for rid in revision_ids]


class DatabaseRevisionRepository(RevisionRepository):
    """
    데이터베이스에 리비전을 저장하는 저장소 구현.

    PostgreSQL 데이터베이스를 사용하여 리비전을 영속적으로 저장한다.
    """

    def __init__(self, session: AsyncSession):
        """
        저장소를 초기화한다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self.session = session

    async def create(self, revision: Revision) -> Revision:
        """
        새로운 리비전을 데이터베이스에 저장한다.

        Args:
            revision: 저장할 리비전

        Returns:
            저장된 리비전
        """
        orm_revision = RevisionORM.from_domain(revision)
        self.session.add(orm_revision)
        await self.session.flush()
        await self.session.commit()
        return orm_revision.to_domain()

    async def get(self, id: str) -> Optional[Revision]:
        """
        주어진 id로 리비전을 조회한다.

        Args:
            id: 조회할 리비전의 고유 식별자

        Returns:
            조회된 리비전 또는 없으면 None
        """
        query = select(RevisionORM).where(RevisionORM.id == id)
        result = await self.session.execute(query)
        orm_revision = result.scalar_one_or_none()
        if orm_revision is None:
            return None
        return orm_revision.to_domain()

    async def list_by_document_id(self, document_id: str) -> list[Revision]:
        """
        주어진 문서의 리비전을 생성 순서대로 나열한다.

        Args:
            document_id: 조회할 문서의 고유 식별자

        Returns:
            문서의 리비전 목록 (생성 순서)
        """
        query = select(RevisionORM).where(
            RevisionORM.document_id == document_id
        ).order_by(RevisionORM.created_at)
        result = await self.session.execute(query)
        orm_revisions = result.scalars().all()
        return [orm_revision.to_domain() for orm_revision in orm_revisions]
