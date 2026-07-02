"""Search module package."""
from modules.search.document import (
    SearchDocument,
    EmptySearchDocumentIdError,
    EmptySearchDocumentTitleError,
)
from modules.search.query import (
    SearchQuery,
    EmptySearchQueryTermError,
    InvalidSearchQueryLimitError,
    InvalidSearchQueryOffsetError,
)
from modules.search.result import (
    SearchResult,
    InvalidSearchResultScoreError,
)
from modules.search.adapter import SearchAdapter
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.meilisearch_adapter import MeilisearchSearchAdapter
from modules.search.opensearch_adapter import OpenSearchSearchAdapter
from modules.search.service import SearchService
from modules.search.job_payload import IndexDocumentJobPayload
from modules.search.reindex import SearchReindexCommand
from modules.search.config import SearchAdapterConfig, InvalidSearchAdapterBackendError
from modules.search.normalization import normalize_korean_text
from modules.search.highlighting import highlight_search_term
from modules.search.errors import SearchServiceError
from modules.search.fixtures import SearchFixtureLoader

# 검색 색인 스키마 버전 상수
SEARCH_INDEX_VERSION = "1.0.0"

__all__ = [
    "SearchDocument",
    "EmptySearchDocumentIdError",
    "EmptySearchDocumentTitleError",
    "SearchQuery",
    "EmptySearchQueryTermError",
    "InvalidSearchQueryLimitError",
    "InvalidSearchQueryOffsetError",
    "SearchResult",
    "InvalidSearchResultScoreError",
    "SearchAdapter",
    "InMemorySearchAdapter",
    "MeilisearchSearchAdapter",
    "OpenSearchSearchAdapter",
    "SearchService",
    "IndexDocumentJobPayload",
    "SearchReindexCommand",
    "SearchAdapterConfig",
    "InvalidSearchAdapterBackendError",
    "normalize_korean_text",
    "highlight_search_term",
    "SearchServiceError",
    "SearchFixtureLoader",
    "SEARCH_INDEX_VERSION",
]
