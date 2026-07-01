"""문서 라우터 테스트."""
import pytest
from fastapi.testclient import TestClient


class TestCreateDocument:
    """문서 생성 엔드포인트 테스트."""

    def test_create_document_with_valid_request(self, client: TestClient):
        """엔드포인트는 유효한 요청으로 문서를 생성한다."""
        response = client.post(
            "/api/documents",
            json={"title": "My Document", "source": "Some content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "My Document"

    def test_create_document_with_duplicate_title_returns_409(self, client: TestClient):
        """엔드포인트는 중복된 제목으로 문서를 생성하면 409를 반환한다."""
        # 첫 번째 문서 생성
        response1 = client.post(
            "/api/documents",
            json={"title": "Duplicate Title", "source": "content"},
        )
        assert response1.status_code == 200

        # 중복된 제목으로 생성 시도
        response2 = client.post(
            "/api/documents",
            json={"title": "Duplicate Title", "source": "content2"},
        )
        assert response2.status_code == 409
        data = response2.json()
        assert "detail" in data

    def test_create_document_with_duplicate_title_different_spacing_returns_409(
        self, client: TestClient
    ):
        """엔드포인트는 정규화 후 중복인 제목도 409를 반환한다."""
        # 첫 번째 문서 생성
        response1 = client.post(
            "/api/documents",
            json={"title": "Duplicate Title", "source": "content"},
        )
        assert response1.status_code == 200

        # 공백이 다른 중복된 제목으로 생성 시도
        response2 = client.post(
            "/api/documents",
            json={"title": "  Duplicate   Title  ", "source": "content2"},
        )
        assert response2.status_code == 409
        data = response2.json()
        assert "detail" in data

    def test_create_document_returns_id_and_title(self, client: TestClient):
        """엔드포인트는 생성된 문서의 id와 title을 반환한다."""
        response = client.post(
            "/api/documents",
            json={"title": "Test Title", "source": "Test content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0
        assert data["title"] == "Test Title"

    def test_create_document_with_different_titles(self, client: TestClient):
        """엔드포인트는 서로 다른 제목의 문서를 생성할 수 있다."""
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

    def test_create_document_with_source_field(self, client: TestClient):
        """엔드포인트는 source 필드를 받을 수 있다."""
        response = client.post(
            "/api/documents",
            json={"title": "Document", "source": "Source content"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "title" in data


class TestGetDocument:
    """문서 조회 엔드포인트 테스트."""

    def test_get_document_by_id_success(self, client: TestClient):
        """엔드포인트는 id로 문서를 조회할 수 있다."""
        # 먼저 문서를 생성한다
        create_response = client.post(
            "/api/documents",
            json={"title": "My Document", "source": "Some content"},
        )
        created_data = create_response.json()
        doc_id = created_data["id"]

        # 생성된 문서를 조회한다
        response = client.get(f"/api/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert data["title"] == "My Document"

    def test_get_document_by_id_returns_404_when_not_found(self, client: TestClient):
        """엔드포인트는 존재하지 않는 id를 조회하면 404를 반환한다."""
        response = client.get("/api/documents/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_document_returns_correct_fields(self, client: TestClient):
        """엔드포인트는 문서의 id와 title을 반환한다."""
        # 문서를 생성한다
        create_response = client.post(
            "/api/documents",
            json={"title": "Test Document", "source": "Test content"},
        )
        created_data = create_response.json()
        doc_id = created_data["id"]

        # 문서를 조회한다
        response = client.get(f"/api/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0
        assert data["title"] == "Test Document"


class TestListRevisions:
    """리비전 목록 조회 엔드포인트 테스트."""

    def test_list_revisions_returns_empty_list_for_document_without_revisions(
        self, client: TestClient
    ):
        """문서에 리비전이 없을 때 빈 목록을 반환한다."""
        response = client.get("/api/documents/nonexistent-doc/revisions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
