"""ACL 권한 종류를 나타내는 열거형."""
from enum import Enum


class Permission(Enum):
    """
    문서에 대해 검사할 수 있는 권한 종류.

    ACL 규칙과 권한 검사는 이 열거형의 값을 통해 어떤 동작에 대한
    권한인지를 구분한다.
    """

    READ = "read"
    EDIT = "edit"
    DISCUSS = "discuss"
    MOVE = "move"
    DELETE = "delete"
    ADMIN = "admin"
