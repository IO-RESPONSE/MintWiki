from app.main import create_app


def test_health_returns_ok() -> None:
    app = create_app()
    route = next(route for route in app.routes if getattr(route, "path", None) == "/health")

    response = route.endpoint()

    assert response["status"] == "ok"
    assert response["app"] == "wiki-engine"
