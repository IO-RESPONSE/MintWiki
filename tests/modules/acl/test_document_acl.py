"""DocumentAcl 도메인 모델 테스트."""
import pytest

from modules.acl.document_acl import DocumentAcl, EmptyDocumentIdError
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType


def _rule(id: str, effect: Effect = Effect.ALLOW) -> Rule:
    return Rule(
        id=id,
        subject_type=SubjectType.ALL,
        permission=Permission.READ,
        effect=effect,
    )


class TestDocumentAclCreation:
    """DocumentAcl 생성 시의 검증 로직을 확인한다."""

    def test_creates_document_acl_without_rules(self):
        acl = DocumentAcl(document_id="doc-1")

        assert acl.document_id == "doc-1"
        assert acl.rules() == []

    def test_creates_document_acl_with_initial_rules(self):
        rules = [_rule("rule-1")]

        acl = DocumentAcl(document_id="doc-1", rules=rules)

        assert acl.rules() == rules

    def test_raises_when_document_id_is_empty(self):
        with pytest.raises(EmptyDocumentIdError):
            DocumentAcl(document_id="")

    def test_raises_when_document_id_is_blank(self):
        with pytest.raises(EmptyDocumentIdError):
            DocumentAcl(document_id="   ")


class TestDocumentAclAddRule:
    """add_rule 메서드로 규칙을 추가할 수 있는지 확인한다."""

    def test_adds_rule_to_document(self):
        acl = DocumentAcl(document_id="doc-1")
        rule = _rule("rule-1")

        acl.add_rule(rule)

        assert acl.rules() == [rule]

    def test_appends_multiple_rules_in_order(self):
        acl = DocumentAcl(document_id="doc-1")
        first = _rule("rule-1")
        second = _rule("rule-2", effect=Effect.DENY)

        acl.add_rule(first)
        acl.add_rule(second)

        assert acl.rules() == [first, second]


class TestDocumentAclRemoveRule:
    """remove_rule 메서드로 규칙을 제거할 수 있는지 확인한다."""

    def test_removes_rule_by_id(self):
        rule = _rule("rule-1")
        acl = DocumentAcl(document_id="doc-1", rules=[rule])

        acl.remove_rule("rule-1")

        assert acl.rules() == []

    def test_removes_only_matching_rule(self):
        first = _rule("rule-1")
        second = _rule("rule-2", effect=Effect.DENY)
        acl = DocumentAcl(document_id="doc-1", rules=[first, second])

        acl.remove_rule("rule-1")

        assert acl.rules() == [second]

    def test_does_nothing_when_rule_id_not_found(self):
        rule = _rule("rule-1")
        acl = DocumentAcl(document_id="doc-1", rules=[rule])

        acl.remove_rule("missing-rule")

        assert acl.rules() == [rule]


class TestDocumentAclRulesIsolation:
    """rules() 메서드가 내부 목록의 복사본을 반환하는지 확인한다."""

    def test_rules_returns_copy_not_internal_list(self):
        acl = DocumentAcl(document_id="doc-1", rules=[_rule("rule-1")])

        result = acl.rules()
        result.append(_rule("rule-2"))

        assert len(acl.rules()) == 1

    def test_initial_rules_list_is_not_aliased(self):
        rules = [_rule("rule-1")]
        acl = DocumentAcl(document_id="doc-1", rules=rules)

        rules.append(_rule("rule-2"))

        assert len(acl.rules()) == 1


class TestDocumentAclHasRules:
    """has_rules 메서드가 규칙 존재 여부를 올바르게 반환하는지 확인한다."""

    def test_returns_false_when_no_rules(self):
        acl = DocumentAcl(document_id="doc-1")

        assert acl.has_rules() is False

    def test_returns_true_when_rules_exist(self):
        acl = DocumentAcl(document_id="doc-1", rules=[_rule("rule-1")])

        assert acl.has_rules() is True
