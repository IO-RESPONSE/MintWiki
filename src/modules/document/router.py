"""문서 API 라우터."""
from fastapi import APIRouter, Depends, HTTPException, Request, status

from modules.document.repository import DatabaseDocumentRepository
from modules.document.schema import CreateDocumentRequest, DocumentResponse
from modules.document.service import DocumentService

# 문서 API 라우터를 생성한다.
# 라우터의 접두사는 main.py에서 등록할 때 지정된다.
router = APIRouter()


async def get_session(request: Request):
    """
    요청에 대한 데이터베이스 세션을 생성한다.

    세션은 요청의 지속 시간 동안 유지된다.
    """
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session


async def get_document_service(
    session=Depends(get_session),
) -> DocumentService:
    """
    문서 서비스를 반환한다.

    데이터베이스 세션을 사용하여 저장소를 생성한다.
    """
    repository = DatabaseDocumentRepository(session)
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
    document = await service.create(request.title)
    return DocumentResponse(id=document.id, title=document.title)


@router.get("/{document_id}", tags=["documents"])
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """
    주어진 id로 문서를 조회한다.

    Args:
        document_id: 조회할 문서의 고유 식별자
        service: 문서 서비스

    Returns:
        조회된 문서의 id와 title

    Raises:
        HTTPException: 문서를 찾을 수 없을 때 404 반환
    """
    document = await service.get(document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다",
        )
    return DocumentResponse(id=document.id, title=document.title)
