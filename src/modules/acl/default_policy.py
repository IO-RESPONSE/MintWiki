"""기본 ACL 정책 정의."""
from typing import List

from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType

PUBLIC_READ_RULE_ID = "default-public-read-allow"
LOGGED_IN_EDIT_RULE_ID = "default-logged-in-edit-allow"


def default_rules() -> List[Rule]:
    """
    모든 네임스페이스에 기본으로 적용할 ACL 규칙 목록을 반환한다.

    익명 사용자를 포함한 누구나 문서를 읽을 수 있도록 허용하는 규칙과,
    로그인한 사용자가 문서를 편집할 수 있도록 허용하는 규칙을 포함한다.
    익명 사용자의 편집을 별도로 거부하는 규칙은 이후 태스크에서 추가된다.
    """
    return [
        Rule(
            id=PUBLIC_READ_RULE_ID,
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
        ),
        Rule(
            id=LOGGED_IN_EDIT_RULE_ID,
            subject_type=SubjectType.ALL,
            permission=Permission.EDIT,
            effect=Effect.ALLOW,
        ),
    ]


def build_default_namespace_acl_defaults() -> NamespaceAclDefaults:
    """기본 정책 규칙이 DEFAULT_NAMESPACE에 등록된 NamespaceAclDefaults를 생성한다."""
    defaults = NamespaceAclDefaults()
    defaults.register(DEFAULT_NAMESPACE, default_rules())
    return defaults
