"""라우트 등록 테스트."""
from app.main import create_app


def test_document_router_is_registered() -> None:
    """문서 라우터가 앱에 등록되었는지 확인한다."""
    app = create_app()
    routes = [route.path for route in app.routes]

    assert "/api/documents/" in routes or any(
        path.startswith("/api/documents") for path in routes
    )


def test_document_routes_exist() -> None:
    """문서 API의 필수 라우트들이 존재하는지 확인한다."""
    app = create_app()
    routes = {(route.path, tuple(route.methods)) for route in app.routes if hasattr(route, "methods")}

    # GET /api/documents/ 라우트 존재 확인
    assert any(
        path == "/api/documents/" and "GET" in methods
        for path, methods in routes
    ), "GET /api/documents/ 라우트가 없습니다"

    # POST /api/documents/ 라우트 존재 확인
    assert any(
        path == "/api/documents/" and "POST" in methods
        for path, methods in routes
    ), "POST /api/documents/ 라우트가 없습니다"


def test_health_route_still_exists() -> None:
    """건강 체크 라우트가 여전히 존재하는지 확인한다."""
    app = create_app()
    routes = [route.path for route in app.routes]

    assert "/health" in routes
