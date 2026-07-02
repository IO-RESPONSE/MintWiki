"""search 패키지 export 테스트."""
import modules.search as search


class TestSearchPackageExports:
    """search 패키지가 정상적으로 import 가능한지 검증한다."""

    def test_package_is_importable(self):
        """search 패키지를 import할 수 있다."""
        assert search is not None

    def test_all_matches_declared_exports(self):
        """__all__ 에 선언된 이름이 실제 모듈 속성으로 존재한다.

        search 모듈은 아직 어댑터/로컬 폴백 검색/인덱싱 계약이 구현되지
        않았으므로(선행 태스크 0242 이후에서 추가 예정) 현재는 export가 없다.
        """
        assert search.__all__ == []
        for name in search.__all__:
            assert hasattr(search, name)
