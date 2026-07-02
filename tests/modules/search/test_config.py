"""검색 어댑터 설정 테스트."""
import pytest

from modules.search.config import SearchAdapterConfig, InvalidSearchAdapterBackendError


class TestSearchAdapterConfig:
    """검색 어댑터 설정 테스트."""

    def test_default_backend_is_in_memory(self):
        """backend를 지정하지 않고 환경 변수도 없으면 in_memory를 사용한다."""
        config = SearchAdapterConfig()

        assert config.backend == "in_memory"

    def test_backend_can_be_specified_explicitly(self):
        """backend를 직접 지정하면 그 값을 사용한다."""
        config = SearchAdapterConfig(backend="in_memory")

        assert config.backend == "in_memory"

    def test_backend_read_from_environment_variable(self, monkeypatch):
        """WIKI_SEARCH_BACKEND 환경 변수로 backend 값을 지정할 수 있다."""
        monkeypatch.setenv("WIKI_SEARCH_BACKEND", "in_memory")

        config = SearchAdapterConfig()

        assert config.backend == "in_memory"

    def test_explicit_backend_overrides_environment_variable(self, monkeypatch):
        """생성자에 직접 넘긴 backend가 환경 변수보다 우선한다."""
        monkeypatch.setenv("WIKI_SEARCH_BACKEND", "unsupported")

        config = SearchAdapterConfig(backend="in_memory")

        assert config.backend == "in_memory"

    def test_unsupported_backend_raises_error(self):
        """지원하지 않는 backend 값을 넘기면 오류가 발생한다."""
        with pytest.raises(InvalidSearchAdapterBackendError):
            SearchAdapterConfig(backend="meilisearch")

    def test_unsupported_backend_from_environment_raises_error(self, monkeypatch):
        """환경 변수로 지원하지 않는 backend 값을 지정해도 오류가 발생한다."""
        monkeypatch.setenv("WIKI_SEARCH_BACKEND", "opensearch")

        with pytest.raises(InvalidSearchAdapterBackendError):
            SearchAdapterConfig()
