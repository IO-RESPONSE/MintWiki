"""검색 모듈 상수 테스트."""
import modules.search as search_module


class TestSearchIndexVersionConstant:
    """검색 색인 버전 상수 테스트."""

    def test_search_index_version_is_defined(self):
        """검색 색인 버전 상수가 정의되어 있다."""
        assert hasattr(search_module, "SEARCH_INDEX_VERSION")

    def test_search_index_version_is_string(self):
        """검색 색인 버전 상수는 문자열 타입이다."""
        assert isinstance(search_module.SEARCH_INDEX_VERSION, str)

    def test_search_index_version_format(self):
        """검색 색인 버전 상수는 semantic versioning 형식이다."""
        version = search_module.SEARCH_INDEX_VERSION
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_search_index_version_is_accessible_from_init(self):
        """검색 모듈의 __init__.py에서 버전 상수가 export되어 있다."""
        from modules.search import SEARCH_INDEX_VERSION
        assert SEARCH_INDEX_VERSION == "1.0.0"
