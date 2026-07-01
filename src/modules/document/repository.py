"""문서 저장소 인터페이스 및 구현."""
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from modules.document.model import Document
from persistence.models import DocumentORM


class DuplicateNormalizedTitleError(Exception):
    """정규화된 제목이 중복될 때 발생하는 예외."""

    pass


class DocumentNotFoundError(Exception):
    """문서를 찾을 수 없을 때 발생하는 예외."""

    pass


class DocumentRepository(ABC):
    """
    문서 저장소의 인터페이스.

    저장소는 문서를 저장하고 검색하는 메서드를 정의한다.
    구체적인 저장소 구현(메모리, 데이터베이스 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def create(self, document: Document) -> Document:
        """
        새로운 문서를 저장소에 저장한다.

        Args:
            document: 저장할 문서

        Returns:
            저장된 문서

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Document]:
        """
        주어진 id로 문서를 조회한다.

        Args:
            id: 조회할 문서의 고유 식별자

        Returns:
            조회된 문서 또는 없으면 None
        """
        pass

    @abstractmethod
    async def get_by_normalized_title(self, normalized_title: str) -> Optional[Document]:
        """
        정규화된 제목으로 문서를 조회한다.

        Args:
            normalized_title: 조회할 문서의 정규화된 제목

        Returns:
            조회된 문서 또는 없으면 None
        """
        pass

    @abstractmethod
    async def update(self, document: Document) -> Document:
        """
        기존 문서를 업데이트한다.

        Args:
            document: 업데이트할 문서

        Returns:
            업데이트된 문서

        Raises:
            다양한 저장소 구현별 예외가 발생할 수 있음
        """
        pass


class InMemoryDocumentRepository(DocumentRepository):
    """
    메모리에 문서를 저장하는 저장소 구현.

    초기 테스트 및 개발 단계에서 사용하기 위한 메모리 기반
    저장소 구현이다. 정규화된 제목의 중복을 방지한다.
    """

    def __init__(self):
        """저장소를 초기화한다."""
        self.documents: dict[str, Document] = {}
        self.normalized_title_to_id: dict[str, str] = {}

    async def create(self, document: Document) -> Document:
        """
        새로운 문서를 저장소에 저장한다.

        정규화된 제목이 이미 존재하면 DuplicateNormalizedTitleError를 발생시킨다.

        Args:
            document: 저장할 문서

        Returns:
            저장된 문서

        Raises:
            DuplicateNormalizedTitleError: 정규화된 제목이 중복된 경우
        """
        if document.normalized_title in self.normalized_title_to_id:
            raise DuplicateNormalizedTitleError(
                f"문서 제목 '{document.normalized_title}'는 이미 존재합니다"
            )

        self.documents[document.id] = document
        self.normalized_title_to_id[document.normalized_title] = document.id
        return document

    async def get(self, id: str) -> Optional[Document]:
        """
        주어진 id로 문서를 조회한다.

        Args:
            id: 조회할 문서의 고유 식별자

        Returns:
            조회된 문서 또는 없으면 None
        """
        return self.documents.get(id)

    async def get_by_normalized_title(self, normalized_title: str) -> Optional[Document]:
        """
        정규화된 제목으로 문서를 조회한다.

        Args:
            normalized_title: 조회할 문서의 정규화된 제목

        Returns:
            조회된 문서 또는 없으면 None
        """
        doc_id = self.normalized_title_to_id.get(normalized_title)
        if doc_id is None:
            return None
        return self.documents.get(doc_id)

    async def update(self, document: Document) -> Document:
        """
        기존 문서를 업데이트한다.

        Args:
            document: 업데이트할 문서

        Returns:
            업데이트된 문서

        Raises:
            DocumentNotFoundError: 문서가 없는 경우
        """
        if document.id not in self.documents:
            raise DocumentNotFoundError(f"문서 id '{document.id}'를 찾을 수 없습니다")
        self.documents[document.id] = document
        return document


class DatabaseDocumentRepository(DocumentRepository):
    """
    데이터베이스에 문서를 저장하는 저장소 구현.

    PostgreSQL 데이터베이스를 사용하여 문서를 영속적으로 저장한다.
    정규화된 제목의 중복을 방지한다.
    """

    def __init__(self, session: AsyncSession):
        """
        저장소를 초기화한다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self.session = session

    async def create(self, document: Document) -> Document:
        """
        새로운 문서를 데이터베이스에 저장한다.

        정규화된 제목이 이미 존재하면 DuplicateNormalizedTitleError를 발생시킨다.

        Args:
            document: 저장할 문서

        Returns:
            저장된 문서

        Raises:
            DuplicateNormalizedTitleError: 정규화된 제목이 중복된 경우
        """
        orm_document = DocumentORM.from_domain(document)
        self.session.add(orm_document)
        try:
            await self.session.flush()
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            if "normalized_title" in str(e):
                raise DuplicateNormalizedTitleError(
                    f"문서 제목 '{document.normalized_title}'는 이미 존재합니다"
                )
            raise
        return orm_document.to_domain()

    async def get(self, id: str) -> Optional[Document]:
        """
        주어진 id로 문서를 조회한다.

        Args:
            id: 조회할 문서의 고유 식별자

        Returns:
            조회된 문서 또는 없으면 None
        """
        query = select(DocumentORM).where(DocumentORM.id == id)
        result = await self.session.execute(query)
        orm_document = result.scalar_one_or_none()
        if orm_document is None:
            return None
        return orm_document.to_domain()

    async def get_by_normalized_title(self, normalized_title: str) -> Optional[Document]:
        """
        정규화된 제목으로 문서를 조회한다.

        Args:
            normalized_title: 조회할 문서의 정규화된 제목

        Returns:
            조회된 문서 또는 없으면 None
        """
        query = select(DocumentORM).where(
            DocumentORM.normalized_title == normalized_title
        )
        result = await self.session.execute(query)
        orm_document = result.scalar_one_or_none()
        if orm_document is None:
            return None
        return orm_document.to_domain()

    async def update(self, document: Document) -> Document:
        """
        데이터베이스에서 기존 문서를 업데이트한다.

        Args:
            document: 업데이트할 문서

        Returns:
            업데이트된 문서

        Raises:
            DocumentNotFoundError: 문서가 없는 경우
        """
        # 문서가 존재하는지 확인
        query = select(DocumentORM).where(DocumentORM.id == document.id)
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        if existing is None:
            raise DocumentNotFoundError(f"문서 id '{document.id}'를 찾을 수 없습니다")

        stmt = (
            update(DocumentORM)
            .where(DocumentORM.id == document.id)
            .values(current_revision_id=document.current_revision_id)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return document
