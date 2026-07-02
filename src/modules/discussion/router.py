"""Discussion 모듈의 HTTP 어댑터: 토론 라우터와 권한 의존성 골격."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from modules.acl.permission import Permission
from modules.acl.router import require_permission
from modules.acl.service import AclService
from modules.discussion.comment import (
    EmptyCommentBodyError,
    EmptyCommentCreatedByError,
)
from modules.discussion.schema import (
    AddCommentRequest,
    CommentResponse,
    CreateThreadRequest,
    ThreadResponse,
)
from modules.discussion.service import DiscussionService
from modules.discussion.thread import (
    EmptyThreadCreatedByError,
    EmptyThreadDocumentIdError,
    EmptyThreadTitleError,
)
from modules.user.block_check_service import BlockCheckService

# 토론 스레드/댓글 라우터. 접두사는 main.py에 등록할 때 지정한다.
# 스레드/댓글 관련 나머지 라우트는 이후 태스크에서 이 라우터에 연결한다.
router = APIRouter()


async def get_discussion_service(request: Request) -> DiscussionService:
    """
    토론 서비스를 반환한다.

    앱 상태(app.state.discussion_service)에 미리 준비된 서비스 인스턴스를
    사용한다. 서비스 인스턴스를 준비하는 절차(저장소 선택 등)는 앱을
    구성하는 쪽(main.py 또는 테스트)의 책임이다.
    """
    return request.app.state.discussion_service


@router.post("/threads", tags=["discussion"])
async def create_thread(
    body: CreateThreadRequest,
    service: DiscussionService = Depends(get_discussion_service),
) -> ThreadResponse:
    """
    새로운 토론 스레드를 생성한다.

    Args:
        body: 스레드 생성 요청 (document_id, title, created_by)
        service: 토론 서비스

    Returns:
        생성된 스레드

    Raises:
        HTTPException: 필수 필드가 비어있는 경우 422 반환
    """
    try:
        thread = await service.create_thread(
            document_id=body.document_id,
            title=body.title,
            created_by=body.created_by,
        )
    except (
        EmptyThreadDocumentIdError,
        EmptyThreadTitleError,
        EmptyThreadCreatedByError,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return ThreadResponse(
        id=thread.id,
        document_id=thread.document_id,
        title=thread.title,
        created_by=thread.created_by,
        status=thread.status,
    )


@router.post("/threads/{thread_id}/comments", tags=["discussion"])
async def add_comment(
    thread_id: str,
    body: AddCommentRequest,
    service: DiscussionService = Depends(get_discussion_service),
) -> CommentResponse:
    """
    토론 스레드에 새로운 댓글을 추가한다.

    Args:
        thread_id: 댓글이 속할 스레드의 id
        body: 댓글 추가 요청 (body, created_by)
        service: 토론 서비스

    Returns:
        생성된 댓글

    Raises:
        HTTPException: 필수 필드가 비어있는 경우 422 반환
    """
    try:
        comment = await service.add_comment(
            thread_id=thread_id,
            body=body.body,
            created_by=body.created_by,
        )
    except (EmptyCommentBodyError, EmptyCommentCreatedByError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return CommentResponse(
        id=comment.id,
        thread_id=comment.thread_id,
        body=comment.body,
        created_by=comment.created_by,
        is_hidden=comment.is_hidden,
    )


def require_discuss_permission(
    acl_service: AclService,
    block_check_service: Optional[BlockCheckService] = None,
):
    """
    토론 참여(Permission.DISCUSS) 권한을 요구하는 라우트 의존성을 생성한다.

    require_permission(Permission.DISCUSS, acl_service, block_check_service) 를
    미리 바인딩해 둔 편의 함수로, 토론 라우터가 스레드/댓글 관련 보호 라우트를
    연결할 때 사용할 자리를 미리 마련해 둔 골격이다. document_acl/네임스페이스를
    요청 경로에서 읽어 연결하는 작업과 실제 토론 라우트에 이 의존성을 연결하는
    작업은 이후 태스크에서 구현한다.

    Args:
        acl_service: 권한 검사에 사용할 AclService
        block_check_service: 로그인 사용자의 차단 여부를 확인할 서비스
            (선택사항, 없으면 차단 여부를 확인하지 않는다)

    Returns:
        FastAPI Depends() 에 전달할 수 있는 의존성 콜러블
    """
    return require_permission(
        Permission.DISCUSS, acl_service, block_check_service=block_check_service
    )
