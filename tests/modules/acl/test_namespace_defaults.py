"""NamespaceAclDefaults 모델 테스트."""
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType


def _rule(id: str, effect: Effect = Effect.ALLOW) -> Rule:
    return Rule(
        id=id,
        subject_type=SubjectType.ALL,
        permission=Permission.READ,
        effect=effect,
    )


class TestNamespaceAclDefaultsRegisterAndGet:
    """네임스페이스별로 등록한 규칙을 그대로 조회할 수 있는지 확인한다."""

    def test_returns_registered_rules_for_namespace(self):
        defaults = NamespaceAclDefaults()
        rules = [_rule("rule-1")]

        defaults.register("Talk", rules)

        assert defaults.get("Talk") == rules

    def test_returns_empty_list_for_unregistered_namespace_without_default(self):
        defaults = NamespaceAclDefaults()

        assert defaults.get("Talk") == []

    def test_get_returns_copy_not_internal_list(self):
        defaults = NamespaceAclDefaults()
        rules = [_rule("rule-1")]
        defaults.register("Talk", rules)

        result = defaults.get("Talk")
        result.append(_rule("rule-2"))

        assert defaults.get("Talk") == rules


class TestNamespaceAclDefaultsFallback:
    """등록되지 않은 네임스페이스가 DEFAULT_NAMESPACE 규칙으로 대체되는지 확인한다."""

    def test_falls_back_to_default_namespace_rules(self):
        defaults = NamespaceAclDefaults()
        default_rules = [_rule("default-rule")]
        defaults.register(DEFAULT_NAMESPACE, default_rules)

        assert defaults.get("Talk") == default_rules

    def test_registered_namespace_overrides_default_namespace_rules(self):
        defaults = NamespaceAclDefaults()
        default_rules = [_rule("default-rule")]
        talk_rules = [_rule("talk-rule", effect=Effect.DENY)]
        defaults.register(DEFAULT_NAMESPACE, default_rules)
        defaults.register("Talk", talk_rules)

        assert defaults.get("Talk") == talk_rules
        assert defaults.get("System") == default_rules
