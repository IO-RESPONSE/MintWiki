"""ACL 모듈의 HTTP 어댑터: 보호된 라우트를 위한 의존성 골격."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Request, status

from modules.acl.decision import Decision
from modules.acl.permission import Permission
from modules.acl.rule import SubjectType
from modules.acl.service import AclService
from modules.user.block_check_service import BlockCheckService

# 인증 절차가 로그인 사용자 id 를 request.state 에 채워 넣을 때 사용할 키.
# 실제로 이 값을 채우는 인증 미들웨어/의존성은 이후 태스크에서 구현한다.
CURRENT_USER_ID_STATE_KEY = "current_user_id"


def require_permission(
    permission: Permission,
    acl_service: AclService,
    block_check_service: Optional[BlockCheckService] = None,
):
    """
    주어진 권한을 요구하는 FastAPI 라우트 의존성을 생성한다.

    request.state 에 로그인 사용자 id(CURRENT_USER_ID_STATE_KEY)가 있으면
    사용자를 대상으로, 없으면 익명 사용자를 대상으로 권한을 검사한다.
    block_check_service 가 주어지고 로그인 사용자가 현재 차단되어 있으면
    ACL 규칙과 무관하게 거부한다. 문서별 ACL(document_acl)이나 네임스페이스를
    요청 경로에서 읽어 연결하는 작업, 그리고 request.state 에 로그인
    사용자를 채워 넣는 인증 절차는 이후 태스크에서 구현한다.

    Args:
        permission: 라우트가 요구하는 권한 종류
        acl_service: 권한 검사에 사용할 AclService
        block_check_service: 로그인 사용자의 차단 여부를 확인할 서비스
            (선택사항, 없으면 차단 여부를 확인하지 않는다)

    Returns:
        FastAPI Depends() 에 전달할 수 있는 의존성 콜러블
    """

    async def dependency(request: Request) -> Decision:
        user_id = getattr(request.state, CURRENT_USER_ID_STATE_KEY, None)

        if user_id and block_check_service is not None:
            blocked = await block_check_service.is_blocked(
                user_id, datetime.now(timezone.utc)
            )
            if blocked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="차단된 사용자는 이 작업을 수행할 수 없습니다",
                )

        if user_id:
            decision = acl_service.check(
                permission=permission,
                subject_type=SubjectType.USER,
                subject_id=user_id,
            )
        else:
            decision = acl_service.check(
                permission=permission,
                subject_type=SubjectType.ANONYMOUS,
            )

        if decision.is_denied():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 작업을 수행할 권한이 없습니다",
            )
        return decision

    return dependency


def require_read_permission(acl_service: AclService):
    """
    문서 읽기(Permission.READ) 권한을 요구하는 라우트 의존성을 생성한다.

    require_permission(Permission.READ, acl_service) 를 미리 바인딩해 둔
    편의 함수로, 문서 라우터가 읽기 보호 라우트를 연결할 때 사용할 자리를
    미리 마련해 둔 골격이다. document_acl/네임스페이스를 요청 경로에서
    읽어 연결하는 작업은 require_permission 과 마찬가지로 이후 태스크에서
    구현한다.

    Args:
        acl_service: 권한 검사에 사용할 AclService

    Returns:
        FastAPI Depends() 에 전달할 수 있는 의존성 콜러블
    """
    return require_permission(Permission.READ, acl_service)


def require_edit_permission(
    acl_service: AclService,
    block_check_service: Optional[BlockCheckService] = None,
):
    """
    문서 편집(Permission.EDIT) 권한을 요구하는 라우트 의존성을 생성한다.

    require_permission(Permission.EDIT, acl_service, block_check_service) 를
    미리 바인딩해 둔 편의 함수. block_check_service 가 주어지면 로그인
    사용자가 차단되어 있는지 함께 확인하여, 차단된 사용자는 ACL 규칙과
    무관하게 편집이 거부된다. document_acl/네임스페이스를 요청 경로에서
    읽어 연결하는 작업은 require_permission 과 마찬가지로 이후 태스크에서
    구현한다.

    Args:
        acl_service: 권한 검사에 사용할 AclService
        block_check_service: 로그인 사용자의 차단 여부를 확인할 서비스
            (선택사항, 없으면 차단 여부를 확인하지 않는다)

    Returns:
        FastAPI Depends() 에 전달할 수 있는 의존성 콜러블
    """
    return require_permission(
        Permission.EDIT, acl_service, block_check_service=block_check_service
    )
