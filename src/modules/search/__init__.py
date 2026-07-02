"""Search module package."""
from modules.search.document import (
    SearchDocument,
    EmptySearchDocumentIdError,
    EmptySearchDocumentTitleError,
)

__all__ = [
    "SearchDocument",
    "EmptySearchDocumentIdError",
    "EmptySearchDocumentTitleError",
]
