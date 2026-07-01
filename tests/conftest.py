"""테스트 설정 및 공유 픽스처."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from persistence.base import Base


@pytest.fixture
def app() -> FastAPI:
    """테스트 앱 인스턴스를 생성한다."""
    app = create_app()

    # 테스트를 위해 인메모리 SQLite 데이터베이스를 사용한다.
    # 비동기 엔진을 생성한다.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # 테스트용 세션 팩토리를 생성한다.
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # 앱의 세션 팩토리를 테스트용으로 교체한다.
    app.state.session_factory = async_session

    # 데이터베이스 테이블을 생성한다.
    import asyncio

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_tables())

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """테스트용 클라이언트를 생성한다."""
    return TestClient(app)
