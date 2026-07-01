"""트랜잭션 관리 헬퍼."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update

from persistence.models import DocumentORM, RevisionORM


class DocumentRevisionTransaction:
    """
    문서와 리비전의 원자적 쓰기를 관리하는 트랜잭션 헬퍼.

    문서 생성과 리비전 생성을 동일 트랜잭션에서 수행하여
    부분 쓰기를 방지한다.
    """

    def __init__(self, session: AsyncSession):
        """
        트랜잭션 헬퍼를 초기화한다.

        Args:
            session: SQLAlchemy AsyncSession 인스턴스
        """
        self.session = session

    async def create_document_with_revision(self, document, revision) -> tuple:
        """
        문서와 초기 리비전을 원자적으로 생성한다.

        문서와 리비전이 같은 트랜잭션에서 저장되어
        부분 쓰기를 방지한다. 정규화된 제목의 중복은
        IntegrityError를 발생시킨다.

        Args:
            document: 생성할 문서 도메인 모델
            revision: 생성할 리비전 도메인 모델

        Returns:
            (저장된 문서 도메인 모델, 저장된 리비전 도메인 모델) 튜플

        Raises:
            IntegrityError: 데이터베이스 무결성 제약 조건 위반
        """
        try:
            orm_document = DocumentORM.from_domain(document)
            orm_revision = RevisionORM.from_domain(revision)

            self.session.add(orm_document)
            self.session.add(orm_revision)

            await self.session.flush()
            await self.session.commit()

            return orm_document.to_domain(), orm_revision.to_domain()
        except IntegrityError as e:
            await self.session.rollback()
            raise

    async def update_document_link_revision(self, document):
        """
        문서의 현재 리비전 링크를 업데이트한다.

        현재 리비전 id를 가진 문서를 원자적으로 업데이트한다.

        Args:
            document: 업데이트할 문서 도메인 모델 (current_revision_id 포함)

        Returns:
            업데이트된 문서 도메인 모델
        """
        stmt = (
            update(DocumentORM)
            .where(DocumentORM.id == document.id)
            .values(current_revision_id=document.current_revision_id)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return document
