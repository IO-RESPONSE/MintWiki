"""만료된 임시 제한(Rule.expires_at) 규칙이 권한 검사에서 무시되는지 검증한다."""
from datetime import datetime, timedelta
from typing import Iterable, List

from modules.acl.document_acl import DocumentAcl
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE, NamespaceAclDefaults
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.service import AclService


def _rule(
    id: str,
    permission: Permission = Permission.READ,
    subject_type: SubjectType = SubjectType.ALL,
    effect: Effect = Effect.ALLOW,
    subject_id=None,
    expires_at=None,
) -> Rule:
    return Rule(
        id=id,
        subject_type=subject_type,
        permission=permission,
        effect=effect,
        subject_id=subject_id,
        expires_at=expires_at,
    )


def _active_rules(rules: Iterable[Rule], now: datetime) -> List[Rule]:
    """주어진 시각 기준으로 만료되지 않은 규칙만 남긴다.

    AclService.check는 now를 알지 못하므로, 만료된 임시 제한 규칙을
    무시하는 책임은 호출자가 Rule.is_expired로 걸러낸 뒤 넘겨야 한다는
    사용 계약을 재현하는 테스트 전용 헬퍼다.
    """
    return [rule for rule in rules if not rule.is_expired(now)]


class TestExpiredDenyRuleIsIgnored:
    """만료된 거부 규칙이 시간 경과 후 더 이상 적용되지 않는지 확인한다."""

    def test_expired_deny_falls_through_to_next_allow_rule(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        service = AclService()
        rules = [
            _rule(
                "temp-deny",
                effect=Effect.DENY,
                expires_at=expires_at,
            ),
            _rule("fallback-allow", effect=Effect.ALLOW),
        ]

        after_expiry = expires_at + timedelta(days=1)
        document_acl = DocumentAcl(
            document_id="doc-1", rules=_active_rules(rules, after_expiry)
        )
        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "fallback-allow"

    def test_deny_still_applies_before_expiry(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        service = AclService()
        rules = [
            _rule(
                "temp-deny",
                effect=Effect.DENY,
                expires_at=expires_at,
            ),
            _rule("fallback-allow", effect=Effect.ALLOW),
        ]

        before_expiry = expires_at - timedelta(minutes=30)
        document_acl = DocumentAcl(
            document_id="doc-1", rules=_active_rules(rules, before_expiry)
        )
        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id == "temp-deny"


class TestExpiredRuleWithoutFallbackDeniesByDefault:
    """만료된 규칙만 있을 때 아무 규칙도 매치되지 않아 기본 거부로 판단하는지 확인한다."""

    def test_expired_allow_rule_no_longer_grants_access(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        service = AclService()
        rules = [
            _rule(
                "temp-allow",
                effect=Effect.ALLOW,
                expires_at=expires_at,
            )
        ]

        after_expiry = expires_at + timedelta(seconds=1)
        document_acl = DocumentAcl(
            document_id="doc-1", rules=_active_rules(rules, after_expiry)
        )
        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id is None

    def test_expiry_is_inclusive_at_exact_expiry_time(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        service = AclService()
        rules = [
            _rule(
                "temp-allow",
                effect=Effect.ALLOW,
                expires_at=expires_at,
            )
        ]

        document_acl = DocumentAcl(
            document_id="doc-1", rules=_active_rules(rules, expires_at)
        )
        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_denied() is True


class TestPermanentRulesAreUnaffectedByExpiryFiltering:
    """expires_at이 없는 영구 규칙은 시각과 무관하게 계속 적용되는지 확인한다."""

    def test_permanent_deny_rule_still_applies_after_arbitrary_time(self):
        service = AclService()
        rules = [_rule("permanent-deny", effect=Effect.DENY)]

        far_future = datetime(2099, 1, 1, 0, 0, 0)
        document_acl = DocumentAcl(
            document_id="doc-1", rules=_active_rules(rules, far_future)
        )
        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
            document_acl=document_acl,
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id == "permanent-deny"


class TestExpiredNamespaceDefaultRuleIsIgnored:
    """네임스페이스 기본 규칙에 걸린 임시 제한도 만료 후 무시되는지 확인한다."""

    def test_expired_namespace_default_deny_falls_back_to_next_rule(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        defaults = NamespaceAclDefaults()
        after_expiry = expires_at + timedelta(days=1)
        defaults.register(
            DEFAULT_NAMESPACE,
            _active_rules(
                [
                    _rule("temp-deny", effect=Effect.DENY, expires_at=expires_at),
                    _rule("fallback-allow", effect=Effect.ALLOW),
                ],
                after_expiry,
            ),
        )
        service = AclService(namespace_defaults=defaults)

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "fallback-allow"
