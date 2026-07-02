"""require_permission 라우트 의존성 골격 테스트."""
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.router import CURRENT_USER_ID_STATE_KEY, require_permission
from modules.acl.service import AclService


def _build_client(acl_service: AclService) -> TestClient:
    """require_permission 으로 보호한 테스트용 라우트를 가진 앱을 만든다."""
    app = FastAPI()

    @app.middleware("http")
    async def _set_current_user(request, call_next):
        # 테스트에서 헤더로 로그인 사용자를 흉내낸다.
        user_id = request.headers.get("X-User-Id")
        if user_id:
            setattr(request.state, CURRENT_USER_ID_STATE_KEY, user_id)
        return await call_next(request)

    @app.get("/protected")
    async def protected(decision=Depends(require_permission(Permission.READ, acl_service))):
        return {"allowed": decision.is_allowed()}

    return TestClient(app)


class TestRequirePermissionDeniesByDefault:
    """일치하는 규칙이 없으면 거부되어 403 을 반환하는지 확인한다."""

    def test_anonymous_request_is_denied_without_rules(self):
        client = _build_client(AclService())

        response = client.get("/protected")

        assert response.status_code == 403
        assert "detail" in response.json()


class TestRequirePermissionAllowsAnonymous:
    """익명 대상 허용 규칙이 있으면 통과하는지 확인한다."""

    def test_anonymous_request_is_allowed_when_rule_grants_all(self):
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                Rule(
                    id="allow-read-all",
                    subject_type=SubjectType.ALL,
                    permission=Permission.READ,
                    effect=Effect.ALLOW,
                )
            ],
        )
        client = _build_client(AclService(namespace_defaults=defaults))

        response = client.get("/protected")

        assert response.status_code == 200
        assert response.json() == {"allowed": True}


class TestRequirePermissionUsesLoggedInUser:
    """로그인한 사용자가 있으면 사용자 대상으로 권한을 검사하는지 확인한다."""

    def test_logged_in_user_matching_rule_is_allowed(self):
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                Rule(
                    id="allow-read-user-1",
                    subject_type=SubjectType.USER,
                    subject_id="user-1",
                    permission=Permission.READ,
                    effect=Effect.ALLOW,
                )
            ],
        )
        client = _build_client(AclService(namespace_defaults=defaults))

        response = client.get("/protected", headers={"X-User-Id": "user-1"})

        assert response.status_code == 200
        assert response.json() == {"allowed": True}

    def test_logged_in_user_without_matching_rule_is_denied(self):
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                Rule(
                    id="allow-read-user-1",
                    subject_type=SubjectType.USER,
                    subject_id="user-1",
                    permission=Permission.READ,
                    effect=Effect.ALLOW,
                )
            ],
        )
        client = _build_client(AclService(namespace_defaults=defaults))

        response = client.get("/protected", headers={"X-User-Id": "user-2"})

        assert response.status_code == 403
