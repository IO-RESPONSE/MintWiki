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
from modules.search.config import SearchAdapterConfig, InvalidSearchAdapterBackendError
from modules.search.normalization import normalize_korean_text

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
    "SearchAdapterConfig",
    "InvalidSearchAdapterBackendError",
    "normalize_korean_text",
]
