"""토론(discussion) 모듈의 남용(abuse) 시나리오 회귀 테스트 자리 표시자(placeholder).

댓글 도배 방지, 모더레이션 권한 강화, 차단 사용자 연동 등 남용 방지 전체
스위트는 아직 만들어지지 않았다. 이 파일은 그보다 앞서, 현재 MVP 단계
(`DiscussionService`/`DiscussionComment`/`router.py`)가 실제로 허용하고
있는 남용 경로 몇 가지를 공격 시나리오 형태로 고정해 두어, 이후 태스크가
관련 코드를 건드릴 때 (의도한 강화인지 우연한 회귀인지) 조기에 구분할 수
있게 하기 위한 자리 표시자다. 각 항목의 세부 근거는
`src/modules/discussion/README.md`의 "Discussion Thread State Machine"과
"Comment Moderation Rules" 절을 참고한다.
"""
from datetime import datetime, timezone
from typing import Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.discussion.audit_event import DiscussionAuditAction
from modules.discussion.comment import DiscussionComment
from modules.discussion.repository import InMemoryDiscussionRepository
from modules.discussion.router import router
from modules.discussion.service import DiscussionService
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


@pytest.fixture
def client() -> TestClient:
    """discussion 라우터만 마운트한 테스트용 앱과 클라이언트를 생성한다.

    실제 배포 시 main.py가 ACL/차단 검사를 추가로 연결할 수도 있지만,
    router.py 자체는 그런 검사를 하나도 강제하지 않는다는 점을 이 파일의
    테스트가 고정해 둔다.
    """
    app = FastAPI()
    app.state.discussion_service = DiscussionService(InMemoryDiscussionRepository())
    app.include_router(router)
    return TestClient(app)


class TestThreadAndCommentCreationHaveNoPermissionOrBlockCheckWired:
    """스레드/댓글 생성 라우트에 권한·차단 검사가 전혀 연결되어 있지 않음을 확인한다."""

    def test_creating_many_threads_without_any_authentication_succeeds(
        self, client: TestClient
    ):
        # 로그인 헤더나 ACL 규칙 없이도 반복 요청이 모두 성공해, 익명
        # 사용자가 스레드를 무제한으로 만들어낼 수 있음을 고정한다.
        responses = [
            client.post(
                "/threads",
                json={"document_id": "doc1", "title": f"제목{i}", "created_by": "anon"},
            )
            for i in range(20)
        ]

        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_blocked_user_id_as_created_by_is_not_checked_against_block_list(
        self, client: TestClient
    ):
        # 실제로 유효한 차단 기록을 가진 사용자 id라도(BlockCheckService로
        # 확인하면 차단 상태임), require_discuss_permission()이 이 라우트에
        # 연결되어 있지 않으므로 차단 여부가 전혀 조회되지 않고 요청이
        # 그대로 성공한다.
        block_repository = _FakeBlockRepository()
        await block_repository.create(
            Block(id="block1", user_id="blocked-user", created_at=datetime.now(timezone.utc))
        )
        block_check_service = BlockCheckService(block_repository)
        assert await block_check_service.is_blocked(
            "blocked-user", datetime.now(timezone.utc)
        ) is True

        response = client.post(
            "/threads",
            json={
                "document_id": "doc1",
                "title": "제목",
                "created_by": "blocked-user",
            },
        )

        assert response.status_code == 200

    def test_flooding_comments_on_a_single_thread_via_http_succeeds(
        self, client: TestClient
    ):
        create_response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "제목", "created_by": "user1"},
        )
        thread_id = create_response.json()["id"]

        responses = [
            client.post(
                f"/threads/{thread_id}/comments",
                json={"body": f"댓글{i}", "created_by": "spammer"},
            )
            for i in range(20)
        ]

        assert all(r.status_code == 200 for r in responses)
        listed = client.get(f"/threads/{thread_id}/comments").json()["comments"]
        assert len(listed) == 20


class TestCommentFloodIgnoresThreadCloseOrPause:
    """닫히거나 일시정지된 스레드도 새 댓글 도배를 막지 못함을 확인한다."""

    @pytest.mark.asyncio
    async def test_flooding_comments_on_closed_thread_succeeds_via_service(self):
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )
        await service.close_thread(thread.id)

        for i in range(10):
            comment = await service.add_comment(
                thread_id=thread.id, body=f"댓글{i}", created_by="spammer"
            )
            assert comment.id is not None

        comments = await service.list_comments_by_thread_id(thread.id)
        assert len(comments) == 10

    @pytest.mark.asyncio
    async def test_flooding_comments_on_paused_thread_succeeds_via_service(self):
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )
        await service.pause_thread(thread.id)

        for i in range(10):
            comment = await service.add_comment(
                thread_id=thread.id, body=f"댓글{i}", created_by="spammer"
            )
            assert comment.id is not None

        comments = await service.list_comments_by_thread_id(thread.id)
        assert len(comments) == 10

    def test_adding_comment_via_http_after_thread_is_closed_still_succeeds(
        self, client: TestClient
    ):
        create_response = client.post(
            "/threads",
            json={"document_id": "doc1", "title": "제목", "created_by": "user1"},
        )
        thread_id = create_response.json()["id"]
        client.post(f"/threads/{thread_id}/close")

        response = client.post(
            f"/threads/{thread_id}/comments",
            json={"body": "닫힌 스레드에 남긴 댓글", "created_by": "spammer"},
        )

        assert response.status_code == 200


class TestHideCommentTrustsCallerSuppliedActorIdentity:
    """hide_comment가 actor_id를 role/소유권 검증 없이 그대로 신뢰함을 확인한다."""

    @pytest.mark.asyncio
    async def test_hide_comment_accepts_arbitrary_actor_id_impersonating_moderator(self):
        # "moderator"라는 문자열을 자칭하는 것만으로 실제 모더레이터 권한이
        # 있는지 검증하지 않고 그대로 받아들여진다.
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="user1"
        )
        comment = await service.add_comment(
            thread_id=thread.id, body="본문", created_by="user2"
        )

        hidden = await service.hide_comment(
            comment.id, actor_id="not-really-a-moderator"
        )

        assert hidden.is_hidden is True
        events = [
            e
            for e in service.audit_recorder.events()
            if e.action is DiscussionAuditAction.COMMENT_HIDDEN
        ]
        assert events[0].actor_id == "not-really-a-moderator"

    @pytest.mark.asyncio
    async def test_hide_comment_succeeds_for_actor_unrelated_to_thread_or_comment(self):
        # 스레드 생성자도, 댓글 작성자도 아닌 제3자가 actor_id로 지정되어도
        # 숨김 처리가 그대로 성공한다 (소유권/역할 검사가 전혀 없음).
        repo = InMemoryDiscussionRepository()
        service = DiscussionService(repo)
        thread = await service.create_thread(
            document_id="doc1", title="제목", created_by="thread-owner"
        )
        comment = await service.add_comment(
            thread_id=thread.id, body="본문", created_by="comment-author"
        )

        hidden = await service.hide_comment(comment.id, actor_id="unrelated-bystander")

        assert hidden.is_hidden is True


class TestModeratorViewExposesHiddenBodyWithNoPermissionGuard:
    """to_moderator_view()가 서비스/ACL 계층을 거치지 않아도 그대로 호출 가능함을 확인한다."""

    def test_any_caller_holding_a_comment_reference_can_read_hidden_body(self):
        # DiscussionService/AclService를 전혀 거치지 않고, DiscussionComment
        # 객체 참조만 있으면 누구든 to_moderator_view()로 숨겨진 본문을
        # 읽을 수 있다.
        comment = DiscussionComment(
            id="c1",
            thread_id="t1",
            body="숨겨진 실제 본문",
            created_by="user1",
            created_at=datetime.now(timezone.utc),
        )
        comment.hide(datetime.now(timezone.utc))

        public_view = comment.to_public_view()
        moderator_view = comment.to_moderator_view()

        assert public_view["body"] is None
        assert moderator_view["body"] == "숨겨진 실제 본문"
