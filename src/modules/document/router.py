"""문서 API 라우터."""
from fastapi import APIRouter

# 문서 API 라우터를 생성한다.
# 라우터의 접두사는 main.py에서 등록할 때 지정된다.
router = APIRouter()


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
async def create_document():
    """
    새로운 문서를 생성한다.

    Returns:
        생성된 문서
    """
    # TODO: 문서 생성 구현 (out of scope)
    pass
