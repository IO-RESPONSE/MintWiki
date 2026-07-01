"""문서 라우터 테스트."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class TestCreateDocument:
    """문서 생성 엔드포인트 테스트."""

    def test_create_document_with_valid_request(self):
        """엔드포인트는 유효한 요청으로 문서를 생성한다."""
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/documents",
            json={"title": "My Document", "source": "Some content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "My Document"

    def test_create_document_returns_id_and_title(self):
        """엔드포인트는 생성된 문서의 id와 title을 반환한다."""
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/documents",
            json={"title": "Test Title", "source": "Test content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0
        assert data["title"] == "Test Title"

    def test_create_document_with_different_titles(self):
        """엔드포인트는 서로 다른 제목의 문서를 생성할 수 있다."""
        app = create_app()
        client = TestClient(app)

        response1 = client.post(
            "/api/documents",
            json={"title": "First Document", "source": "content1"},
        )
        response2 = client.post(
            "/api/documents",
            json={"title": "Second Document", "source": "content2"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        assert data1["id"] != data2["id"]
        assert data1["title"] == "First Document"
        assert data2["title"] == "Second Document"

    def test_create_document_with_source_field(self):
        """엔드포인트는 source 필드를 받을 수 있다."""
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/documents",
            json={"title": "Document", "source": "Source content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "title" in data
