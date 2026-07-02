"""search 패키지 export 테스트."""
import modules.search as search


class TestSearchPackageExports:
    """search 패키지가 정상적으로 import 가능한지 검증한다."""

    def test_package_is_importable(self):
        """search 패키지를 import할 수 있다."""
        assert search is not None

    def test_all_matches_declared_exports(self):
        """__all__ 에 선언된 이름이 실제 모듈 속성으로 존재한다.

        어댑터/로컬 폴백 검색/인덱싱 계약은 후속 태스크에서 추가되므로,
        현재는 검색 문서 모델(SearchDocument)과 검색 질의 모델(SearchQuery),
        그리고 그 오류 타입만 export한다.
        """
        assert search.__all__ == [
            "SearchDocument",
            "EmptySearchDocumentIdError",
            "EmptySearchDocumentTitleError",
            "SearchQuery",
            "EmptySearchQueryTermError",
        ]
        for name in search.__all__:
            assert hasattr(search, name)
