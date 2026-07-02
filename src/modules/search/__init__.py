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
from modules.search.service import SearchService
from modules.search.job_payload import IndexDocumentJobPayload
from modules.search.config import SearchAdapterConfig, InvalidSearchAdapterBackendError

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
    "SearchService",
    "IndexDocumentJobPayload",
    "SearchAdapterConfig",
    "InvalidSearchAdapterBackendError",
]
