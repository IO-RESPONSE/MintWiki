"""AclService 골격 테스트."""
from modules.acl.document_acl import DocumentAcl
from modules.acl.namespace_defaults import NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.service import AclService


def _rule(
    id: str,
    permission: Permission = Permission.READ,
    subject_type: SubjectType = SubjectType.ALL,
    effect: Effect = Effect.ALLOW,
    subject_id=None,
) -> Rule:
    return Rule(
        id=id,
        subject_type=subject_type,
        permission=permission,
        effect=effect,
        subject_id=subject_id,
    )


class TestAclServiceWithoutRules:
    """일치하는 규칙이 전혀 없을 때 거부로 판단하는지 확인한다."""

    def test_denies_when_no_rules_registered(self):
        service = AclService()

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id is None

    def test_denies_when_namespace_has_no_matching_rules(self):
        service = AclService(namespace_defaults=NamespaceAclDefaults())

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            namespace="Talk",
        )

        assert decision.is_denied() is True


class TestAclServiceUsesDocumentAcl:
    """문서에 등록된 ACL 규칙이 있으면 그 규칙을 우선 적용하는지 확인한다."""

    def test_uses_matching_document_rule(self):
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1", rules=[_rule("rule-1", effect=Effect.ALLOW)]
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "rule-1"

    def test_ignores_rule_for_different_permission(self):
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[_rule("rule-1", permission=Permission.EDIT)],
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_denied() is True

    def test_ignores_rule_for_different_subject(self):
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule("rule-1", subject_type=SubjectType.USER, subject_id="user-1")
            ],
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.USER,
            subject_id="user-2",
            document_acl=document_acl,
        )

        assert decision.is_denied() is True


class TestAclServiceFallsBackToNamespaceDefaults:
    """문서 ACL이 없거나 규칙이 비어 있으면 네임스페이스 기본 규칙을 사용하는지 확인한다."""

    def test_uses_namespace_default_when_document_acl_missing(self):
        defaults = NamespaceAclDefaults()
        defaults.register("Talk", [_rule("default-rule", effect=Effect.DENY)])
        service = AclService(namespace_defaults=defaults)

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            namespace="Talk",
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id == "default-rule"

    def test_uses_namespace_default_when_document_acl_has_no_rules(self):
        defaults = NamespaceAclDefaults()
        defaults.register("Talk", [_rule("default-rule", effect=Effect.ALLOW)])
        service = AclService(namespace_defaults=defaults)
        empty_document_acl = DocumentAcl(document_id="doc-1")

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=empty_document_acl,
            namespace="Talk",
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "default-rule"


class TestAclServiceRuleOrder:
    """여러 규칙이 있을 때 먼저 등록된 규칙이 우선 적용되는지 확인한다."""

    def test_first_matching_rule_wins(self):
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule("rule-1", effect=Effect.DENY),
                _rule("rule-2", effect=Effect.ALLOW),
            ],
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id == "rule-1"
