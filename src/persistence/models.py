"""SQLAlchemy ORM 모델 정의."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func

from persistence.base import Base


class DocumentORM(Base):
    """
    문서를 나타내는 ORM 모델.

    이 모델은 문서 테이블을 SQLAlchemy를 통해 매핑한다.
    도메인 모델과 데이터베이스 테이블 사이의 변환을 담당한다.
    """

    __tablename__ = "document"

    id = Column(String(255), primary_key=True, nullable=False)
    title = Column(String(500), nullable=False)
    normalized_title = Column(String(500), nullable=False, unique=True)
    current_revision_id = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def to_domain(self):
        """
        ORM 모델을 도메인 모델로 변환한다.

        Returns:
            Document: 도메인 모델 인스턴스
        """
        from modules.document.model import Document

        return Document(
            id=self.id,
            title=self.title,
            current_revision_id=self.current_revision_id,
        )

    @staticmethod
    def from_domain(document):
        """
        도메인 모델을 ORM 모델로 변환한다.

        Args:
            document: Document 도메인 모델

        Returns:
            DocumentORM: ORM 모델 인스턴스
        """
        return DocumentORM(
            id=document.id,
            title=document.title,
            normalized_title=document.normalized_title,
            current_revision_id=document.current_revision_id,
        )


class RevisionORM(Base):
    """
    리비전을 나타내는 ORM 모델.

    이 모델은 리비전 테이블을 SQLAlchemy를 통해 매핑한다.
    도메인 모델과 데이터베이스 테이블 사이의 변환을 담당한다.
    """

    __tablename__ = "revision"

    id = Column(String(255), primary_key=True, nullable=False)
    document_id = Column(
        String(255),
        ForeignKey("document.id", name="fk_revision_document_id"),
        nullable=False,
    )
    source = Column(Text, nullable=False)
    author_id = Column(String(255), nullable=False)
    summary = Column(String(500), nullable=False)
    parent_revision_id = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def to_domain(self):
        """
        ORM 모델을 도메인 모델로 변환한다.

        Returns:
            Revision: 도메인 모델 인스턴스
        """
        from modules.revision.model import Revision

        return Revision(
            id=self.id,
            document_id=self.document_id,
            source=self.source,
            author_id=self.author_id,
            summary=self.summary,
            parent_revision_id=self.parent_revision_id,
        )

    @staticmethod
    def from_domain(revision):
        """
        도메인 모델을 ORM 모델로 변환한다.

        Args:
            revision: Revision 도메인 모델

        Returns:
            RevisionORM: ORM 모델 인스턴스
        """
        return RevisionORM(
            id=revision.id,
            document_id=revision.document_id,
            source=revision.source,
            author_id=revision.author_id,
            summary=revision.summary,
            parent_revision_id=revision.parent_revision_id,
        )


class AuditEventORM(Base):
    """
    감사 이벤트를 나타내는 ORM 모델.

    이 모델은 감사 이벤트 테이블을 SQLAlchemy를 통해 매핑한다.
    도메인 모델과 데이터베이스 테이블 사이의 변환을 담당한다.
    Append-only 특성으로 인해 update_at 컬럼이 없다.
    """

    __tablename__ = "audit_event"

    id = Column(String(255), primary_key=True, nullable=False)
    category = Column(String(20), nullable=False)
    action = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)
    related_entity_id = Column(String(255), nullable=True)
    actor_id = Column(String(255), nullable=True)
    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def to_domain(self):
        """
        ORM 모델을 도메인 모델로 변환한다.

        Returns:
            AuditEvent: 도메인 모델 인스턴스
        """
        from modules.audit.audit_event import AuditEvent

        return AuditEvent(
            id=self.id,
            category=self.category,
            action=self.action,
            entity_id=self.entity_id,
            related_entity_id=self.related_entity_id,
            actor_id=self.actor_id,
            occurred_at=self.occurred_at,
        )

    @staticmethod
    def from_domain(event):
        """
        도메인 모델을 ORM 모델로 변환한다.

        Args:
            event: AuditEvent 도메인 모델

        Returns:
            AuditEventORM: ORM 모델 인스턴스
        """
        return AuditEventORM(
            id=event.id,
            category=event.category,
            action=event.action,
            entity_id=event.entity_id,
            related_entity_id=event.related_entity_id,
            actor_id=event.actor_id,
            occurred_at=event.occurred_at,
        )


class SchemaVersionORM(Base):
    """
    배포된 스키마 버전을 나타내는 ORM 모델.

    스키마 버전 테이블을 SQLAlchemy를 통해 매핑한다.
    현재 배포된 스키마 버전을 추적한다.
    """

    __tablename__ = "schema_version"

    version = Column(String(255), primary_key=True, nullable=False)
    applied_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
