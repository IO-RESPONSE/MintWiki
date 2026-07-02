"""parse_namespace로 얻은 네임스페이스가 NamespaceAclDefaults/AclService의
기본값 대체(fallback)와 올바르게 맞물리는지 확인한다."""
from modules.acl.default_policy import (
    LOGGED_IN_EDIT_RULE_ID,
    PUBLIC_READ_RULE_ID,
    build_default_namespace_acl_defaults,
)
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.namespace_parser import parse_namespace
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.service import AclService


def _rule(id: str, permission: Permission, effect: Effect) -> Rule:
    return Rule(id=id, subject_type=SubjectType.ALL, permission=permission, effect=effect)


class TestParsedNamespaceFallsBackToDefaultRules:
    """구분자가 없는 제목의 네임스페이스가 DEFAULT_NAMESPACE 규칙으로 대체되는지 확인한다."""

    def test_title_without_namespace_uses_default_namespace_rules(self):
        namespace = parse_namespace("PageName")
        defaults = build_default_namespace_acl_defaults()
        service = AclService(namespace_defaults=defaults)

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ANONYMOUS,
            namespace=namespace,
        )

        assert namespace == DEFAULT_NAMESPACE
        assert decision.is_allowed() is True
        assert decision.matched_rule_id == PUBLIC_READ_RULE_ID

    def test_title_with_unregistered_namespace_falls_back_to_default_rules(self):
        namespace = parse_namespace("Talk:PageName")
        defaults = build_default_namespace_acl_defaults()
        service = AclService(namespace_defaults=defaults)

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.USER,
            subject_id="user-1",
            namespace=namespace,
        )

        assert namespace == "Talk"
        assert decision.is_allowed() is True
        assert decision.matched_rule_id == LOGGED_IN_EDIT_RULE_ID


class TestParsedNamespaceUsesRegisteredOverrideInsteadOfDefault:
    """네임스페이스가 별도로 등록되어 있으면 기본값 대체 없이 그 규칙을 사용하는지 확인한다."""

    def test_registered_namespace_overrides_default_fallback(self):
        namespace = parse_namespace("System:PageName")
        defaults = build_default_namespace_acl_defaults()
        defaults.register(
            "System", [_rule("system-read-deny", Permission.READ, Effect.DENY)]
        )
        service = AclService(namespace_defaults=defaults)

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ANONYMOUS,
            namespace=namespace,
        )

        assert namespace == "System"
        assert decision.is_denied() is True
        assert decision.matched_rule_id == "system-read-deny"

    def test_other_namespace_still_falls_back_to_default_after_override_registered(self):
        namespace = parse_namespace("Talk:PageName")
        defaults = build_default_namespace_acl_defaults()
        defaults.register(
            "System", [_rule("system-read-deny", Permission.READ, Effect.DENY)]
        )
        service = AclService(namespace_defaults=defaults)

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ANONYMOUS,
            namespace=namespace,
        )

        assert namespace == "Talk"
        assert decision.is_allowed() is True
        assert decision.matched_rule_id == PUBLIC_READ_RULE_ID


class TestNamespaceFallbackWithoutDefaultRegistered:
    """DEFAULT_NAMESPACE에 아무 규칙도 등록되어 있지 않으면 빈 규칙으로 대체되어 거부되는지 확인한다."""

    def test_falls_back_to_empty_rules_and_denies(self):
        namespace = parse_namespace("PageName")
        service = AclService(namespace_defaults=NamespaceAclDefaults())

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            namespace=namespace,
        )

        assert namespace == DEFAULT_NAMESPACE
        assert decision.is_denied() is True
        assert decision.matched_rule_id is None
