"""AclAuditRecorder 서비스 테스트."""
from modules.acl.audit_event import AclAuditAction
from modules.acl.audit_recorder import AclAuditRecorder
from modules.acl.document_acl import DocumentAcl
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType


def _rule(id: str, effect: Effect = Effect.ALLOW) -> Rule:
    return Rule(
        id=id,
        subject_type=SubjectType.ALL,
        permission=Permission.READ,
        effect=effect,
    )


class TestAclAuditRecorderRecordRuleAdded:
    """record_rule_added가 규칙을 추가하고 감사 이벤트를 남기는지 확인한다."""

    def test_adds_rule_to_document_acl(self):
        recorder = AclAuditRecorder()
        document_acl = DocumentAcl(document_id="doc-1")
        rule = _rule("rule-1")

        recorder.record_rule_added(document_acl, rule)

        assert document_acl.rules() == [rule]

    def test_records_rule_added_event(self):
        recorder = AclAuditRecorder()
        document_acl = DocumentAcl(document_id="doc-1")
        rule = _rule("rule-1")

        event = recorder.record_rule_added(document_acl, rule, actor_id="user-1")

        assert event.action is AclAuditAction.RULE_ADDED
        assert event.rule_id == "rule-1"
        assert event.document_id == "doc-1"
        assert event.actor_id == "user-1"
        assert recorder.events() == [event]

    def test_records_event_without_actor_id(self):
        recorder = AclAuditRecorder()
        document_acl = DocumentAcl(document_id="doc-1")
        rule = _rule("rule-1")

        event = recorder.record_rule_added(document_acl, rule)

        assert event.actor_id is None


class TestAclAuditRecorderRecordRuleRemoved:
    """record_rule_removed가 규칙을 제거하고 감사 이벤트를 남기는지 확인한다."""

    def test_removes_rule_from_document_acl(self):
        recorder = AclAuditRecorder()
        rule = _rule("rule-1")
        document_acl = DocumentAcl(document_id="doc-1", rules=[rule])

        recorder.record_rule_removed(document_acl, "rule-1")

        assert document_acl.rules() == []

    def test_records_rule_removed_event(self):
        recorder = AclAuditRecorder()
        rule = _rule("rule-1")
        document_acl = DocumentAcl(document_id="doc-1", rules=[rule])

        event = recorder.record_rule_removed(
            document_acl, "rule-1", actor_id="user-2"
        )

        assert event.action is AclAuditAction.RULE_REMOVED
        assert event.rule_id == "rule-1"
        assert event.document_id == "doc-1"
        assert event.actor_id == "user-2"
        assert recorder.events() == [event]


class TestAclAuditRecorderEventsAccumulate:
    """여러 변경이 발생하면 이벤트가 순서대로 누적되는지 확인한다."""

    def test_accumulates_events_across_multiple_changes(self):
        recorder = AclAuditRecorder()
        document_acl = DocumentAcl(document_id="doc-1")
        rule = _rule("rule-1")

        added_event = recorder.record_rule_added(document_acl, rule)
        removed_event = recorder.record_rule_removed(document_acl, "rule-1")

        assert recorder.events() == [added_event, removed_event]

    def test_events_returns_copy_not_internal_list(self):
        recorder = AclAuditRecorder()
        document_acl = DocumentAcl(document_id="doc-1")
        recorder.record_rule_added(document_acl, _rule("rule-1"))

        result = recorder.events()
        result.clear()

        assert len(recorder.events()) == 1
