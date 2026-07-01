"""테스트 설정 및 공유 픽스처."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    """테스트 앱 인스턴스를 생성한다."""
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """테스트용 클라이언트를 생성한다."""
    return TestClient(app)
