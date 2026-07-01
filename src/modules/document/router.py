"""문서 API 라우터."""
from fastapi import APIRouter, Depends

from modules.document.repository import InMemoryDocumentRepository
from modules.document.schema import CreateDocumentRequest, DocumentResponse
from modules.document.service import DocumentService

# 문서 API 라우터를 생성한다.
# 라우터의 접두사는 main.py에서 등록할 때 지정된다.
router = APIRouter()


def get_document_service() -> DocumentService:
    """문서 서비스를 생성하여 반환한다."""
    repository = InMemoryDocumentRepository()
    return DocumentService(repository)


@router.get("/", tags=["documents"])
async def list_documents():
    """
    모든 문서를 조회한다.

    Returns:
        문서 목록
    """
    # TODO: 문서 목록 조회 구현 (out of scope)
    pass


@router.post("/", tags=["documents"])
async def create_document(
    request: CreateDocumentRequest,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """
    새로운 문서를 생성한다.

    Args:
        request: 문서 생성 요청 (title, source)
        service: 문서 서비스

    Returns:
        생성된 문서의 id와 title
    """
    document = service.create(request.title)
    return DocumentResponse(id=document.id, title=document.title)
