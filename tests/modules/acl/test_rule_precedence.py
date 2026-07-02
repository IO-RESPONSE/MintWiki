"""AclService의 규칙 우선순위(등록 순서 기반 first-match) 동작을 검증한다."""
import pytest

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


class TestFirstMatchWinsRegardlessOfEffectCombination:
    """먼저 등록된 규칙의 effect가 무엇이든 그대로 채택되는지 확인한다."""

    @pytest.mark.parametrize(
        "first_effect,second_effect",
        [
            (Effect.DENY, Effect.ALLOW),
            (Effect.ALLOW, Effect.DENY),
            (Effect.ALLOW, Effect.ALLOW),
            (Effect.DENY, Effect.DENY),
        ],
    )
    def test_first_rule_effect_determines_decision(self, first_effect, second_effect):
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule("rule-first", effect=first_effect),
                _rule("rule-second", effect=second_effect),
            ],
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.matched_rule_id == "rule-first"
        assert decision.is_allowed() == (first_effect is Effect.ALLOW)


class TestOrderOverridesSpecificity:
    """규칙 우선순위는 등록 순서로만 결정되며 대상의 구체성과는 무관함을 확인한다."""

    def test_general_rule_before_specific_rule_wins_even_though_less_specific(self):
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule("all-deny", subject_type=SubjectType.ALL, effect=Effect.DENY),
                _rule(
                    "user-allow",
                    subject_type=SubjectType.USER,
                    subject_id="user-1",
                    effect=Effect.ALLOW,
                ),
            ],
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.USER,
            subject_id="user-1",
            document_acl=document_acl,
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id == "all-deny"

    def test_specific_rule_before_general_rule_wins(self):
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "user-allow",
                    subject_type=SubjectType.USER,
                    subject_id="user-1",
                    effect=Effect.ALLOW,
                ),
                _rule("all-deny", subject_type=SubjectType.ALL, effect=Effect.DENY),
            ],
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.USER,
            subject_id="user-1",
            document_acl=document_acl,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "user-allow"


class TestNonMatchingRulesAreSkippedInOrder:
    """대상이나 권한이 일치하지 않는 규칙은 건너뛰고 다음 규칙을 검사하는지 확인한다."""

    def test_skips_rules_for_other_permissions_and_subjects_until_match(self):
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule("edit-rule", permission=Permission.EDIT, effect=Effect.DENY),
                _rule(
                    "other-user-rule",
                    subject_type=SubjectType.USER,
                    subject_id="user-2",
                    effect=Effect.DENY,
                ),
                _rule(
                    "matching-rule",
                    subject_type=SubjectType.USER,
                    subject_id="user-1",
                    effect=Effect.ALLOW,
                ),
            ],
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.USER,
            subject_id="user-1",
            document_acl=document_acl,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "matching-rule"


class TestDocumentAclFullyOverridesNamespaceDefaults:
    """문서 ACL이 존재하면 일치하는 규칙이 없어도 네임스페이스 기본값으로 대체되지 않음을 확인한다."""

    def test_non_matching_document_rule_denies_without_falling_back(self):
        defaults = NamespaceAclDefaults()
        defaults.register(
            "Talk", [_rule("namespace-default-allow", effect=Effect.ALLOW)]
        )
        service = AclService(namespace_defaults=defaults)
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[_rule("edit-only", permission=Permission.EDIT, effect=Effect.ALLOW)],
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
            namespace="Talk",
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id is None

    def test_document_rule_takes_precedence_over_conflicting_namespace_default(self):
        defaults = NamespaceAclDefaults()
        defaults.register("Talk", [_rule("namespace-default-deny", effect=Effect.DENY)])
        service = AclService(namespace_defaults=defaults)
        document_acl = DocumentAcl(
            document_id="doc-1", rules=[_rule("document-allow", effect=Effect.ALLOW)]
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
            namespace="Talk",
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "document-allow"
