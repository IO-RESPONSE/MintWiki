from fastapi import FastAPI

from app.config import get_settings
from app.database import get_session_factory, create_document_repository
from modules.document.router import router as document_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    # 세션 팩토리를 생성하고 앱 상태에 저장한다.
    app.state.session_factory = get_session_factory(settings)

    # 문서 저장소 팩토리를 앱 상태에 저장한다.
    app.state.document_repository_factory = create_document_repository

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.environment,
        }

    app.include_router(document_router, prefix="/api/documents")

    return app


app = create_app()

