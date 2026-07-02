"""Decision 도메인 모델 테스트."""
from modules.acl.decision import Decision
from modules.acl.permission import Permission


class TestDecisionCreation:
    """Decision 생성 시 필드가 올바르게 설정되는지 확인한다."""

    def test_creates_allowed_decision(self):
        decision = Decision(
            permission=Permission.READ,
            allowed=True,
            reason="matched allow rule",
            matched_rule_id="rule-1",
        )

        assert decision.permission is Permission.READ
        assert decision.allowed is True
        assert decision.reason == "matched allow rule"
        assert decision.matched_rule_id == "rule-1"

    def test_creates_denied_decision_without_matched_rule(self):
        decision = Decision(
            permission=Permission.EDIT,
            allowed=False,
            reason="no matching rule",
        )

        assert decision.permission is Permission.EDIT
        assert decision.allowed is False
        assert decision.reason == "no matching rule"
        assert decision.matched_rule_id is None


class TestDecisionIsAllowed:
    """is_allowed 메서드가 허용 여부를 올바르게 반환하는지 확인한다."""

    def test_returns_true_when_allowed(self):
        decision = Decision(permission=Permission.READ, allowed=True, reason="ok")

        assert decision.is_allowed() is True

    def test_returns_false_when_not_allowed(self):
        decision = Decision(permission=Permission.READ, allowed=False, reason="denied")

        assert decision.is_allowed() is False


class TestDecisionIsDenied:
    """is_denied 메서드가 허용 여부의 반대를 올바르게 반환하는지 확인한다."""

    def test_returns_false_when_allowed(self):
        decision = Decision(permission=Permission.READ, allowed=True, reason="ok")

        assert decision.is_denied() is False

    def test_returns_true_when_not_allowed(self):
        decision = Decision(permission=Permission.READ, allowed=False, reason="denied")

        assert decision.is_denied() is True
