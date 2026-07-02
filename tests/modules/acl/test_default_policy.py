"""기본 ACL 정책(공개 읽기 허용) 테스트."""
from modules.acl.default_policy import (
    PUBLIC_READ_RULE_ID,
    build_default_namespace_acl_defaults,
    default_rules,
)
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE
from modules.acl.permission import Permission
from modules.acl.rule import SubjectType
from modules.acl.service import AclService


class TestDefaultRules:
    """default_rules가 공개 읽기 허용 규칙을 포함하는지 확인한다."""

    def test_contains_public_read_allow_rule(self):
        rules = default_rules()

        assert len(rules) == 1
        rule = rules[0]
        assert rule.id == PUBLIC_READ_RULE_ID
        assert rule.permission is Permission.READ
        assert rule.subject_type is SubjectType.ALL
        assert rule.is_allow() is True

    def test_returns_new_list_each_call(self):
        first = default_rules()
        first.append(None)

        assert len(default_rules()) == 1


class TestBuildDefaultNamespaceAclDefaults:
    """기본 정책이 DEFAULT_NAMESPACE에 등록되는지 확인한다."""

    def test_registers_public_read_rule_under_default_namespace(self):
        defaults = build_default_namespace_acl_defaults()

        rules = defaults.get(DEFAULT_NAMESPACE)

        assert len(rules) == 1
        assert rules[0].id == PUBLIC_READ_RULE_ID

    def test_applies_to_any_namespace_via_fallback(self):
        defaults = build_default_namespace_acl_defaults()

        rules = defaults.get("Talk")

        assert len(rules) == 1
        assert rules[0].id == PUBLIC_READ_RULE_ID


class TestDefaultPolicyWithAclService:
    """기본 정책을 사용하는 AclService가 익명 사용자의 읽기를 허용하는지 확인한다."""

    def test_allows_anonymous_read_by_default(self):
        service = AclService(namespace_defaults=build_default_namespace_acl_defaults())

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ANONYMOUS,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == PUBLIC_READ_RULE_ID

    def test_allows_authenticated_user_read_by_default(self):
        service = AclService(namespace_defaults=build_default_namespace_acl_defaults())

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.USER,
            subject_id="user-1",
        )

        assert decision.is_allowed() is True

    def test_does_not_allow_edit_by_default(self):
        service = AclService(namespace_defaults=build_default_namespace_acl_defaults())

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.ANONYMOUS,
        )

        assert decision.is_denied() is True
