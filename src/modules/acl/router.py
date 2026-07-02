"""ACL 모듈의 HTTP 어댑터: 보호된 라우트를 위한 의존성 골격."""
from fastapi import HTTPException, Request, status

from modules.acl.decision import Decision
from modules.acl.permission import Permission
from modules.acl.rule import SubjectType
from modules.acl.service import AclService

# 인증 절차가 로그인 사용자 id 를 request.state 에 채워 넣을 때 사용할 키.
# 실제로 이 값을 채우는 인증 미들웨어/의존성은 이후 태스크에서 구현한다.
CURRENT_USER_ID_STATE_KEY = "current_user_id"


def require_permission(permission: Permission, acl_service: AclService):
    """
    주어진 권한을 요구하는 FastAPI 라우트 의존성을 생성한다.

    request.state 에 로그인 사용자 id(CURRENT_USER_ID_STATE_KEY)가 있으면
    사용자를 대상으로, 없으면 익명 사용자를 대상으로 권한을 검사한다.
    문서별 ACL(document_acl)이나 네임스페이스를 요청 경로에서 읽어 연결하는
    작업, 그리고 request.state 에 로그인 사용자를 채워 넣는 인증 절차는
    이후 태스크에서 구현한다. 이 골격은 검사 결과가 거부일 때 403 을
    반환하는 기본 동작만 제공한다.

    Args:
        permission: 라우트가 요구하는 권한 종류
        acl_service: 권한 검사에 사용할 AclService

    Returns:
        FastAPI Depends() 에 전달할 수 있는 의존성 콜러블
    """

    async def dependency(request: Request) -> Decision:
        user_id = getattr(request.state, CURRENT_USER_ID_STATE_KEY, None)
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
