"""ACL 규칙 도메인 모델."""
from enum import Enum
from typing import Optional

from modules.acl.permission import Permission


class SubjectType(Enum):
    """
    ACL 규칙이 적용되는 대상의 종류.

    규칙은 특정 사용자, 특정 그룹, 익명 사용자, 또는 모든 사용자를
    대상으로 지정할 수 있다.
    """

    USER = "user"
    GROUP = "group"
    ANONYMOUS = "anonymous"
    ALL = "all"


class Effect(Enum):
    """규칙이 권한을 허용하는지 거부하는지를 나타낸다."""

    ALLOW = "allow"
    DENY = "deny"


class EmptyRuleIdError(Exception):
    """규칙 id가 비어있을 때 발생."""

    pass


class MissingSubjectIdError(Exception):
    """대상 종류가 USER 또는 GROUP인데 subject_id가 없을 때 발생."""

    pass


class Rule:
    """
    문서에 대한 하나의 ACL 규칙을 나타내는 도메인 모델.

    규칙은 대상(subject_type/subject_id), 검사 대상 권한(permission),
    그리고 허용/거부 여부(effect)로 구성된다. 여러 규칙을 조합해 최종
    접근 허용 여부를 판단하는 로직은 이 모델이 아닌 상위 서비스가 담당한다.
    """

    def __init__(
        self,
        id: str,
        subject_type: SubjectType,
        permission: Permission,
        effect: Effect,
        subject_id: Optional[str] = None,
    ):
        """
        ACL 규칙을 생성한다.

        Args:
            id: 규칙의 고유 식별자
            subject_type: 규칙이 적용되는 대상의 종류
            permission: 규칙이 검사하는 권한 종류
            effect: 권한을 허용할지 거부할지 여부
            subject_id: 대상이 USER 또는 GROUP일 때의 사용자/그룹 id

        Raises:
            EmptyRuleIdError: 규칙 id가 비어있거나 공백만 있는 경우
            MissingSubjectIdError: 대상 종류가 USER 또는 GROUP인데
                subject_id가 없는 경우
        """
        if not id or not id.strip():
            raise EmptyRuleIdError("규칙 id는 비어있을 수 없습니다")
        if subject_type in (SubjectType.USER, SubjectType.GROUP) and not subject_id:
            raise MissingSubjectIdError(
                "대상 종류가 사용자 또는 그룹인 경우 subject_id가 필요합니다"
            )

        self.id = id
        self.subject_type = subject_type
        self.subject_id = subject_id
        self.permission = permission
        self.effect = effect

    def is_allow(self) -> bool:
        """규칙이 허용 규칙인지 확인한다."""
        return self.effect is Effect.ALLOW

    def applies_to(
        self, subject_type: SubjectType, subject_id: Optional[str] = None
    ) -> bool:
        """주어진 대상이 이 규칙의 적용 대상인지 확인한다."""
        if self.subject_type is SubjectType.ALL:
            return True
        if self.subject_type is not subject_type:
            return False
        if self.subject_type in (SubjectType.USER, SubjectType.GROUP):
            return self.subject_id == subject_id
        return True
