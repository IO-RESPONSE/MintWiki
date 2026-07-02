"""토론 라우터 골격 테스트."""
from fastapi import APIRouter

from modules.discussion.router import router


class TestDiscussionRouterSkeleton:
    """router 객체가 라우트 없는 APIRouter로 준비되어 있는지 확인한다."""

    def test_router_is_an_api_router(self):
        assert isinstance(router, APIRouter)

    def test_router_has_no_routes_yet(self):
        # 실제 스레드/댓글 라우트는 이후 태스크에서 추가된다.
        assert router.routes == []
