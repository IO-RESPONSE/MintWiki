"""차단된 사용자가 편집할 수 없는지 종단 간(end-to-end)으로 확인하는 테스트.

require_edit_permission 의존성에 AclService 와 BlockCheckService 를 함께
연결했을 때, 차단 여부에 따라 편집 요청이 어떻게 처리되는지에 집중한다.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.router import (
    CURRENT_USER_ID_STATE_KEY,
    require_edit_permission,
    require_read_permission,
)
from modules.acl.service import AclService
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


def _allow_all_defaults(permission: Permission) -> NamespaceAclDefaults:
    """주어진 권한을 누구에게나 허용하는 네임스페이스 기본 규칙을 만든다."""
    defaults = NamespaceAclDefaults()
    defaults.register(
        DEFAULT_NAMESPACE,
        [
            Rule(
                id=f"allow-{permission.value}-all",
                subject_type=SubjectType.ALL,
                permission=permission,
                effect=Effect.ALLOW,
            )
        ],
    )
    return defaults


def _build_client(
    acl_service: AclService, block_check_service: BlockCheckService
) -> TestClient:
    """편집은 차단 검사와 함께, 읽기는 차단 검사 없이 보호한 테스트용 앱을 만든다."""
    app = FastAPI()

    @app.middleware("http")
    async def _set_current_user(request, call_next):
        # 테스트에서 헤더로 로그인 사용자를 흉내낸다.
        user_id = request.headers.get("X-User-Id")
        if user_id:
            setattr(request.state, CURRENT_USER_ID_STATE_KEY, user_id)
        return await call_next(request)

    @app.get("/document/edit")
    async def edit_document(
        decision=Depends(require_edit_permission(acl_service, block_check_service))
    ):
        return {"allowed": decision.is_allowed()}

    @app.get("/document/read")
    async def read_document(decision=Depends(require_read_permission(acl_service))):
        return {"allowed": decision.is_allowed()}

    return TestClient(app)


class TestBlockedUserCannotEditIndefinitely:
    """만료 시각이 없는(무기한) 차단을 받은 사용자는 편집할 수 없는지 확인한다."""

    def test_indefinitely_blocked_user_is_denied_edit(self):
        repository = _FakeBlockRepository()
        asyncio.run(
            repository.create(
                Block(id="block1", user_id="user-1", created_at=datetime(2026, 1, 1))
            )
        )
        client = _build_client(
            AclService(namespace_defaults=_allow_all_defaults(Permission.EDIT)),
            BlockCheckService(repository),
        )

        response = client.get("/document/edit", headers={"X-User-Id": "user-1"})

        assert response.status_code == 403


class TestBlockedUserCannotEditBeforeExpiry:
    """만료 시각 이전의 차단을 받은 사용자는 편집할 수 없는지 확인한다."""

    def test_temporarily_blocked_user_is_denied_edit_before_expiry(self):
        # router 는 datetime.now(timezone.utc) 기준으로 만료 여부를 판단하므로
        # 현재 시각을 기준으로 미래의 만료 시각을 가진 차단을 등록한다.
        now = datetime.now(timezone.utc)
        created_at = now - timedelta(days=1)
        expires_at = now + timedelta(days=7)
        repository = _FakeBlockRepository()
        asyncio.run(
            repository.create(
                Block(
                    id="block1",
                    user_id="user-1",
                    created_at=created_at,
                    expires_at=expires_at,
                )
            )
        )
        client = _build_client(
            AclService(namespace_defaults=_allow_all_defaults(Permission.EDIT)),
            BlockCheckService(repository),
        )

        response = client.get("/document/edit", headers={"X-User-Id": "user-1"})

        assert response.status_code == 403


class TestFormerlyBlockedUserCanEditAfterExpiry:
    """차단이 만료된 사용자는 다시 편집할 수 있는지 확인한다."""

    def test_user_can_edit_once_block_has_expired(self):
        # router 는 datetime.now(timezone.utc) 기준으로 만료 여부를 판단하므로
        # 현재 시각보다 과거인 만료 시각을 가진 차단을 등록해 둔다.
        now = datetime.now(timezone.utc)
        created_at = now - timedelta(days=2)
        expires_at = now - timedelta(days=1)
        repository = _FakeBlockRepository()
        asyncio.run(
            repository.create(
                Block(
                    id="block1",
                    user_id="user-1",
                    created_at=created_at,
                    expires_at=expires_at,
                )
            )
        )
        client = _build_client(
            AclService(namespace_defaults=_allow_all_defaults(Permission.EDIT)),
            BlockCheckService(repository),
        )

        response = client.get("/document/edit", headers={"X-User-Id": "user-1"})

        assert response.status_code == 200
        assert response.json() == {"allowed": True}


class TestBlockDoesNotAffectOtherUsers:
    """한 사용자의 차단이 다른 사용자의 편집을 막지 않는지 확인한다."""

    def test_other_user_can_still_edit_when_someone_else_is_blocked(self):
        repository = _FakeBlockRepository()
        asyncio.run(
            repository.create(
                Block(id="block1", user_id="user-1", created_at=datetime(2026, 1, 1))
            )
        )
        client = _build_client(
            AclService(namespace_defaults=_allow_all_defaults(Permission.EDIT)),
            BlockCheckService(repository),
        )

        response = client.get("/document/edit", headers={"X-User-Id": "user-2"})

        assert response.status_code == 200
        assert response.json() == {"allowed": True}


class TestBlockedUserCanStillRead:
    """차단은 편집만 막을 뿐, 읽기 권한에는 영향을 주지 않는지 확인한다."""

    def test_blocked_user_can_still_read_document(self):
        repository = _FakeBlockRepository()
        asyncio.run(
            repository.create(
                Block(id="block1", user_id="user-1", created_at=datetime(2026, 1, 1))
            )
        )
        acl_service = AclService(
            namespace_defaults=_allow_all_defaults(Permission.READ)
        )
        client = _build_client(acl_service, BlockCheckService(repository))

        edit_response = client.get("/document/edit", headers={"X-User-Id": "user-1"})
        read_response = client.get("/document/read", headers={"X-User-Id": "user-1"})

        assert edit_response.status_code == 403
        assert read_response.status_code == 200
        assert read_response.json() == {"allowed": True}
