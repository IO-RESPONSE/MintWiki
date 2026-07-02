"""ACL 우회 시도 회귀 테스트 자리 표시자(placeholder).

`docs/roadmap.md`의 Phase 8(Hardening)에 예정된 "ACL bypass tests"의 전체
스위트는 아직 만들어지지 않았다. 이 파일은 그보다 앞서, 현재 MVP 단계
(`AclService`/`router.py`/`Rule`)가 이미 보장하는 우회 방지 동작 몇 가지를
공격 시나리오 형태로 고정해 두어, 이후 태스크가 관련 코드를 건드릴 때
회귀를 조기에 잡아내기 위한 자리 표시자다. 각 규칙의 세부 근거는
`src/modules/acl/README.md`(ACL Evaluation Order)와
`src/modules/user/README.md`(User Identity Boundaries)를 참고한다.
"""
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from modules.acl.document_acl import DocumentAcl
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.router import CURRENT_USER_ID_STATE_KEY, require_permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.service import AclService


def _rule(
    id: str,
    permission: Permission = Permission.READ,
    subject_type: SubjectType = SubjectType.ALL,
    effect: Effect = Effect.ALLOW,
    subject_id=None,
) -> Rule:
    return Rule(
        id=id,
        subject_type=subject_type,
        permission=permission,
        effect=effect,
        subject_id=subject_id,
    )


def _build_client(acl_service: AclService, *, wire_user_header: bool) -> TestClient:
    """`X-User-Id` 헤더를 request.state로 옮기는 미들웨어를 선택적으로 연결한다.

    wire_user_header=False 는, 인증 절차를 거치지 않고 클라이언트가 임의로
    보낸 헤더값이 실제로 로그인 사용자로 인정되지는 않는 상황을 재현한다.
    """
    app = FastAPI()

    if wire_user_header:

        @app.middleware("http")
        async def _set_current_user(request, call_next):
            user_id = request.headers.get("X-User-Id")
            if user_id:
                setattr(request.state, CURRENT_USER_ID_STATE_KEY, user_id)
            return await call_next(request)

    @app.get("/protected")
    async def protected(
        decision=Depends(require_permission(Permission.EDIT, acl_service))
    ):
        return {"allowed": decision.is_allowed()}

    return TestClient(app)


class TestAnonymousRequestCannotForgeUserIdentity:
    """인증 절차를 거치지 않은 헤더값만으로는 로그인 사용자로 인정되지 않는지 확인한다."""

    def _allow_user_admin_edit(self) -> AclService:
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                _rule(
                    "allow-admin-edit",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.USER,
                    subject_id="admin",
                    effect=Effect.ALLOW,
                )
            ],
        )
        return AclService(namespace_defaults=defaults)

    def test_unwired_header_does_not_grant_forged_user_access(self):
        # request.state에 로그인 사용자를 채워 넣는 미들웨어가 없으므로,
        # 헤더에 "admin"을 실어 보내도 익명 요청으로 취급되어야 한다.
        client = _build_client(self._allow_user_admin_edit(), wire_user_header=False)

        response = client.get("/protected", headers={"X-User-Id": "admin"})

        assert response.status_code == 403

    def test_same_header_succeeds_once_auth_middleware_wires_it(self):
        # 대조군: 동일한 규칙과 헤더값이라도, 실제 인증 절차가 request.state를
        # 채워 넣으면 정상적으로 허용되어야 한다 (규칙 자체는 문제가 없음을 확인).
        client = _build_client(self._allow_user_admin_edit(), wire_user_header=True)

        response = client.get("/protected", headers={"X-User-Id": "admin"})

        assert response.status_code == 200
        assert response.json() == {"allowed": True}


class TestEmptyUserIdIsTreatedAsAnonymousNotAsWildcardMatch:
    """로그인 사용자 id가 빈 문자열이면 익명으로 취급되고, 어떤 USER 규칙과도 매칭되지 않는지 확인한다."""

    def test_blank_user_id_falls_back_to_anonymous_and_is_denied(self):
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                _rule(
                    "allow-someone-edit",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.USER,
                    subject_id="user-1",
                    effect=Effect.ALLOW,
                )
            ],
        )
        acl_service = AclService(namespace_defaults=defaults)
        app = FastAPI()

        @app.middleware("http")
        async def _set_blank_current_user(request, call_next):
            # 상위 인증 계층의 버그 등으로 사용자 id가 빈 문자열로 채워지는
            # 경우를 재현한다.
            setattr(request.state, CURRENT_USER_ID_STATE_KEY, "")
            return await call_next(request)

        @app.get("/protected")
        async def protected(
            decision=Depends(require_permission(Permission.EDIT, acl_service))
        ):
            return {"allowed": decision.is_allowed()}

        client = TestClient(app)

        response = client.get("/protected")

        assert response.status_code == 403


class TestGroupScopedRuleDoesNotMatchUserWithSameId:
    """사용자 id와 그룹 id가 우연히 같은 문자열이어도 서로의 규칙을 빌려오지 못하는지 확인한다."""

    def test_user_sharing_group_id_is_not_granted_group_rule(self):
        # "editors"라는 이름의 그룹에 대한 허용 규칙만 있고, 이 문자열과
        # 우연히 같은 id를 가진 사용자가 로그인한 상황을 재현한다.
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-editors-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id="editors",
                    effect=Effect.ALLOW,
                )
            ],
        )

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.USER,
            subject_id="editors",
            document_acl=document_acl,
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id is None

    def test_actual_group_subject_type_still_matches_the_same_rule(self):
        # 대조군: 동일한 id라도 SubjectType.GROUP으로 검사하면 정상적으로
        # 매칭되어야 한다 (규칙 자체는 문제가 없음을 확인).
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-editors-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id="editors",
                    effect=Effect.ALLOW,
                )
            ],
        )

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.GROUP,
            subject_id="editors",
            document_acl=document_acl,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "group-editors-allow"


class TestDocumentAclWithUnrelatedRuleDoesNotBorrowMorePermissiveNamespaceDefault:
    """문서 ACL에 다른 권한 규칙만 있어도, 더 관대한 네임스페이스 기본값을 빌려오지 못하는지 확인한다."""

    def _service_with_permissive_edit_default(self) -> AclService:
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                _rule(
                    "namespace-allow-edit-all",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.ALL,
                    effect=Effect.ALLOW,
                )
            ],
        )
        return AclService(namespace_defaults=defaults)

    def test_document_acl_covering_only_read_denies_edit_despite_permissive_default(self):
        service = self._service_with_permissive_edit_default()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "document-allow-read-all",
                    permission=Permission.READ,
                    subject_type=SubjectType.ALL,
                    effect=Effect.ALLOW,
                )
            ],
        )

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id is None

    def test_same_service_allows_edit_when_no_document_acl_is_given(self):
        # 대조군: 문서 ACL 없이 검사하면 네임스페이스 기본값이 정상적으로
        # 적용되어야 한다 (규칙 자체는 문제가 없음을 확인).
        service = self._service_with_permissive_edit_default()

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.ALL,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "namespace-allow-edit-all"
