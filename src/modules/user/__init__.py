"""User module package."""
from modules.user.model import EmptyUsernameError, User

__all__ = [
    "User",
    "EmptyUsernameError",
]
