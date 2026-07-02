"""검색 모듈의 HTTP 어댑터: 제목 검색 API, 본문 검색 API."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from modules.search.query import EmptySearchQueryTermError, SearchQuery
from modules.search.schema import (
    SearchHealthResponse,
    SearchResponse,
    SearchResultResponse,
)
from modules.search.service import SearchService

# 검색 API 라우터. 접두사는 main.py에 등록할 때 지정한다.
# 색인 관련 라우트는 이후 태스크에서 이 라우터에 연결한다.
router = APIRouter()


async def get_search_service(request: Request) -> SearchService:
    """
    검색 서비스를 반환한다.

    앱 상태(app.state.search_service)에 미리 준비된 서비스 인스턴스를
    사용한다. 서비스 인스턴스를 준비하는 절차(어댑터 선택 등)는 앱을
    구성하는 쪽(main.py 또는 테스트)의 책임이다.
    """
    return request.app.state.search_service


@router.get("/title", tags=["search"])
async def search_by_title(
    title: str = Query(...),
    limit: Optional[int] = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """
    제목 검색 질의어로 문서를 검색한다.

    Args:
        title: 검색 질의어 (쿼리 파라미터)
        limit: 반환할 최대 결과 개수 (쿼리 파라미터, 선택사항)
        offset: 건너뛸 결과 개수 (쿼리 파라미터, 기본값 0)
        service: 검색 서비스

    Returns:
        질의어와 관련된 검색 결과 목록

    Raises:
        HTTPException: 질의어가 비어있는 경우 422 반환
    """
    try:
        query = SearchQuery(term=title, limit=limit, offset=offset)
    except EmptySearchQueryTermError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    results = await service.search(query)
    return SearchResponse(
        results=[
            SearchResultResponse(
                document_id=result.document.document_id,
                title=result.document.title,
                score=result.score,
            )
            for result in results
        ]
    )


@router.get("/health", tags=["search"])
async def search_health(
    service: SearchService = Depends(get_search_service),
) -> SearchHealthResponse:
    """
    검색 백엔드의 상태를 확인하는 자리표시자 라우트.

    SearchService.health_check()의 결과를 그대로 응답에 담아 전달할 뿐,
    그 외의 처리는 하지 않는다. 검색 백엔드 장애를 구분되는 HTTP 상태
    코드(예: 503)로 매핑하는 것은 이후 태스크에서 채워진다.

    Args:
        service: 검색 서비스

    Returns:
        검색 백엔드가 정상이면 healthy=True, 그렇지 않으면 healthy=False
    """
    healthy = await service.health_check()
    return SearchHealthResponse(healthy=healthy)


@router.get("/body", tags=["search"])
async def search_by_body(
    body: str = Query(...),
    limit: Optional[int] = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """
    본문 검색 질의어로 문서를 검색한다.

    Args:
        body: 검색 질의어 (쿼리 파라미터)
        limit: 반환할 최대 결과 개수 (쿼리 파라미터, 선택사항)
        offset: 건너뛸 결과 개수 (쿼리 파라미터, 기본값 0)
        service: 검색 서비스

    Returns:
        질의어와 관련된 검색 결과 목록

    Raises:
        HTTPException: 질의어가 비어있는 경우 422 반환
    """
    try:
        query = SearchQuery(term=body, limit=limit, offset=offset)
    except EmptySearchQueryTermError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    results = await service.search(query)
    return SearchResponse(
        results=[
            SearchResultResponse(
                document_id=result.document.document_id,
                title=result.document.title,
                score=result.score,
            )
            for result in results
        ]
    )
