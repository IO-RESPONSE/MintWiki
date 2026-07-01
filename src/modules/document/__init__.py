"""Document module package."""
from modules.document.repository import (
    DuplicateNormalizedTitleError,
    DocumentNotFoundError,
)

__all__ = [
    "DuplicateNormalizedTitleError",
    "DocumentNotFoundError",
]
