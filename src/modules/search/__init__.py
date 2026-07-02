"""Search module package."""
from modules.search.document import (
    SearchDocument,
    EmptySearchDocumentIdError,
    EmptySearchDocumentTitleError,
)
from modules.search.query import (
    SearchQuery,
    EmptySearchQueryTermError,
)
from modules.search.result import (
    SearchResult,
    InvalidSearchResultScoreError,
)
from modules.search.adapter import SearchAdapter
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.service import SearchService

__all__ = [
    "SearchDocument",
    "EmptySearchDocumentIdError",
    "EmptySearchDocumentTitleError",
    "SearchQuery",
    "EmptySearchQueryTermError",
    "SearchResult",
    "InvalidSearchResultScoreError",
    "SearchAdapter",
    "InMemorySearchAdapter",
    "SearchService",
]
