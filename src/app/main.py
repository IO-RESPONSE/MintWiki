from fastapi import FastAPI

from app.config import get_settings
from modules.document.router import router as document_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

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

