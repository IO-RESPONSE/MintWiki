"""Document module package."""
from modules.document.protection import Protection
from modules.document.protection_repository import ProtectionRepository
from modules.document.repository import (
    DuplicateNormalizedTitleError,
    DocumentNotFoundError,
)

__all__ = [
    "DuplicateNormalizedTitleError",
    "DocumentNotFoundError",
    "Protection",
    "ProtectionRepository",
]
