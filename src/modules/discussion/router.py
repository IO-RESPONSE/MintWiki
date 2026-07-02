"""Discussion 모듈의 HTTP 어댑터: 토론 라우터와 권한 의존성 골격."""
from typing import Optional

from fastapi import APIRouter

from modules.acl.permission import Permission
from modules.acl.router import require_permission
from modules.acl.service import AclService
from modules.user.block_check_service import BlockCheckService

# 토론 스레드/댓글 라우터. 접두사는 main.py에 등록할 때 지정한다.
# 실제 스레드/댓글 라우트는 이후 태스크에서 이 라우터에 연결한다.
router = APIRouter()


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
