"""require_discuss_permission 편의 의존성 골격 테스트."""
import asyncio
from datetime import datetime
from typing import Dict, Optional

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.router import CURRENT_USER_ID_STATE_KEY
from modules.acl.service import AclService
from modules.discussion.router import require_discuss_permission
from modules.user.block import Block
from modules.user.block_check_service import BlockCheckService
from modules.user.block_repository import BlockRepository


class _FakeBlockRepository(BlockRepository):
    """테스트용 메모리 기반 차단 저장소."""

    def __init__(self):
        self._blocks_by_user_id: Dict[str, Block] = {}

    async def create(self, block: Block) -> Block:
        self._blocks_by_user_id[block.user_id] = block
        return block

    async def get(self, id: str) -> Optional[Block]:
        for block in self._blocks_by_user_id.values():
            if block.id == id:
                return block
        return None

    async def get_by_user_id(self, user_id: str) -> Optional[Block]:
        return self._blocks_by_user_id.get(user_id)

    async def delete(self, id: str) -> None:
        for user_id, block in list(self._blocks_by_user_id.items()):
            if block.id == id:
                del self._blocks_by_user_id[user_id]


def _build_client(
    acl_service: AclService,
    block_check_service: Optional[BlockCheckService] = None,
) -> TestClient:
    """require_discuss_permission 으로 보호한 테스트용 라우트를 가진 앱을 만든다."""
    app = FastAPI()

    @app.middleware("http")
    async def _set_current_user(request, call_next):
        # 테스트에서 헤더로 로그인 사용자를 흉내낸다.
        user_id = request.headers.get("X-User-Id")
        if user_id:
            setattr(request.state, CURRENT_USER_ID_STATE_KEY, user_id)
        return await call_next(request)

    @app.get("/discussion")
    async def discussion(
        decision=Depends(require_discuss_permission(acl_service, block_check_service))
    ):
        return {"allowed": decision.is_allowed()}

    return TestClient(app)


class TestRequireDiscussPermissionDeniesByDefault:
    """일치하는 규칙이 없으면 거부되어 403 을 반환하는지 확인한다."""

    def test_anonymous_request_is_denied_without_rules(self):
        client = _build_client(AclService())

        response = client.get("/discussion")

        assert response.status_code == 403
        assert "detail" in response.json()

    def test_authenticated_request_is_denied_without_rules(self):
        # 로그인 사용자도 일치하는 규칙이 없으면 익명 사용자와 동일하게 거부되어야 한다.
        client = _build_client(AclService())

        response = client.get("/discussion", headers={"X-User-Id": "user-1"})

        assert response.status_code == 403
        assert "detail" in response.json()


class TestRequireDiscussPermissionAllowsAnonymous:
    """익명 대상 토론 허용 규칙이 있으면 통과하는지 확인한다."""

    def test_anonymous_request_is_allowed_when_rule_grants_all(self):
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                Rule(
                    id="allow-discuss-all",
                    subject_type=SubjectType.ALL,
                    permission=Permission.DISCUSS,
                    effect=Effect.ALLOW,
                )
            ],
        )
        client = _build_client(AclService(namespace_defaults=defaults))

        response = client.get("/discussion")

        assert response.status_code == 200
        assert response.json() == {"allowed": True}


class TestRequireDiscussPermissionIgnoresOtherPermissions:
    """토론 이외의 권한 규칙만 있으면 거부되는지 확인한다."""

    def test_read_only_rule_does_not_grant_discuss(self):
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

        response = client.get("/discussion")

        assert response.status_code == 403


class TestRequireDiscussPermissionDeniesBlockedUser:
    """차단된 로그인 사용자는 ACL 허용 규칙이 있어도 토론 참여가 거부되는지 확인한다."""

    def test_blocked_user_is_denied_even_when_acl_allows(self):
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                Rule(
                    id="allow-discuss-all",
                    subject_type=SubjectType.ALL,
                    permission=Permission.DISCUSS,
                    effect=Effect.ALLOW,
                )
            ],
        )
        repository = _FakeBlockRepository()
        asyncio.run(
            repository.create(
                Block(id="block1", user_id="user-1", created_at=datetime(2026, 1, 1))
            )
        )
        client = _build_client(
            AclService(namespace_defaults=defaults),
            block_check_service=BlockCheckService(repository),
        )

        response = client.get("/discussion", headers={"X-User-Id": "user-1"})

        assert response.status_code == 403
        assert "detail" in response.json()


class TestRequireDiscussPermissionAllowsUnblockedUser:
    """차단 서비스가 연결되어 있어도 차단되지 않은 사용자는 토론 참여가 허용되는지 확인한다."""

    def test_unblocked_user_is_allowed_when_acl_allows(self):
        defaults = NamespaceAclDefaults()
        defaults.register(
            DEFAULT_NAMESPACE,
            [
                Rule(
                    id="allow-discuss-all",
                    subject_type=SubjectType.ALL,
                    permission=Permission.DISCUSS,
                    effect=Effect.ALLOW,
                )
            ],
        )
        client = _build_client(
            AclService(namespace_defaults=defaults),
            block_check_service=BlockCheckService(_FakeBlockRepository()),
        )

        response = client.get("/discussion", headers={"X-User-Id": "user-1"})

        assert response.status_code == 200
        assert response.json() == {"allowed": True}
