from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from modules.document.repository import DocumentRepository, DatabaseDocumentRepository


def build_engine(settings: Settings):
    """Create a database engine from settings."""
    return create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )


def get_session_factory(settings: Settings) -> sessionmaker:
    """Create a session factory from settings."""
    engine = build_engine(settings)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def create_document_repository(session: AsyncSession) -> DocumentRepository:
    """
    문서 저장소를 생성한다.

    데이터베이스 세션을 사용하여 저장소를 초기화한다.

    Args:
        session: SQLAlchemy AsyncSession 인스턴스

    Returns:
        DocumentRepository 인스턴스
    """
    return DatabaseDocumentRepository(session)
