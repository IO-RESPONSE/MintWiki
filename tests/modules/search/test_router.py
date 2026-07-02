"""검색 라우터 골격 테스트."""
from fastapi import APIRouter

from modules.search.router import router


class TestSearchRouterSkeleton:
    """router 객체가 라우트 없는 APIRouter로 준비되어 있는지 확인한다."""

    def test_router_is_an_api_router(self):
        assert isinstance(router, APIRouter)

    def test_router_has_no_routes_yet(self):
        # 실제 검색/색인 라우트는 이후 태스크에서 추가된다.
        assert router.routes == []
