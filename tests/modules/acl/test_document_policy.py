"""문서 단위 편집/읽기/토론 제한 정책(restrict_document_edit, restrict_document_read,
restrict_document_discuss) 테스트."""
from modules.acl.default_policy import (
    LOGGED_IN_EDIT_RULE_ID,
    PUBLIC_READ_RULE_ID,
    build_default_namespace_acl_defaults,
)
from modules.acl.document_policy import (
    DOCUMENT_DISCUSS_RESTRICTION_RULE_ID,
    DOCUMENT_EDIT_RESTRICTION_RULE_ID,
    DOCUMENT_READ_RESTRICTION_RULE_ID,
    restrict_document_discuss,
    restrict_document_edit,
    restrict_document_read,
)
from modules.acl.permission import Permission
from modules.acl.rule import SubjectType
from modules.acl.service import AclService


class TestRestrictDocumentEdit:
    """restrict_document_edit이 지정한 대상에게만 편집 규칙을 부여하는지 확인한다."""

    def test_returns_document_acl_with_single_edit_rule(self):
        acl = restrict_document_edit(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="editors",
        )

        assert acl.document_id == "doc-1"
        rules = acl.rules()
        assert len(rules) == 1
        rule = rules[0]
        assert rule.id == DOCUMENT_EDIT_RESTRICTION_RULE_ID
        assert rule.permission is Permission.EDIT
        assert rule.subject_type is SubjectType.GROUP
        assert rule.subject_id == "editors"
        assert rule.is_allow() is True


class TestRestrictDocumentEditWithAclService:
    """제한된 문서 ACL이 AclService 검사에서 실제로 편집을 제한하는지 확인한다."""

    def test_allows_the_designated_group_to_edit(self):
        service = AclService()
        acl = restrict_document_edit(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="editors",
        )

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.GROUP,
            subject_id="editors",
            document_acl=acl,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == DOCUMENT_EDIT_RESTRICTION_RULE_ID

    def test_denies_a_different_group_from_editing(self):
        service = AclService()
        acl = restrict_document_edit(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="editors",
        )

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.GROUP,
            subject_id="visitors",
            document_acl=acl,
        )

        assert decision.is_denied() is True

    def test_overrides_default_logged_in_edit_allow_for_other_users(self):
        service = AclService(namespace_defaults=build_default_namespace_acl_defaults())
        acl = restrict_document_edit(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="editors",
        )

        default_decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.USER,
            subject_id="user-1",
        )
        restricted_decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.USER,
            subject_id="user-1",
            document_acl=acl,
        )

        assert default_decision.is_allowed() is True
        assert default_decision.matched_rule_id == LOGGED_IN_EDIT_RULE_ID
        assert restricted_decision.is_denied() is True

    def test_denies_anonymous_users_from_editing(self):
        service = AclService()
        acl = restrict_document_edit(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="editors",
        )

        decision = service.check(
            permission=Permission.EDIT,
            subject_type=SubjectType.ANONYMOUS,
            document_acl=acl,
        )

        assert decision.is_denied() is True


class TestRestrictDocumentRead:
    """restrict_document_read가 지정한 대상에게만 읽기 규칙을 부여하는지 확인한다."""

    def test_returns_document_acl_with_single_read_rule(self):
        acl = restrict_document_read(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="readers",
        )

        assert acl.document_id == "doc-1"
        rules = acl.rules()
        assert len(rules) == 1
        rule = rules[0]
        assert rule.id == DOCUMENT_READ_RESTRICTION_RULE_ID
        assert rule.permission is Permission.READ
        assert rule.subject_type is SubjectType.GROUP
        assert rule.subject_id == "readers"
        assert rule.is_allow() is True


class TestRestrictDocumentReadWithAclService:
    """제한된 문서 ACL이 AclService 검사에서 실제로 읽기를 제한하는지 확인한다."""

    def test_allows_the_designated_group_to_read(self):
        service = AclService()
        acl = restrict_document_read(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="readers",
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.GROUP,
            subject_id="readers",
            document_acl=acl,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == DOCUMENT_READ_RESTRICTION_RULE_ID

    def test_denies_a_different_group_from_reading(self):
        service = AclService()
        acl = restrict_document_read(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="readers",
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.GROUP,
            subject_id="visitors",
            document_acl=acl,
        )

        assert decision.is_denied() is True

    def test_overrides_default_public_read_allow_for_other_users(self):
        service = AclService(namespace_defaults=build_default_namespace_acl_defaults())
        acl = restrict_document_read(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="readers",
        )

        default_decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.USER,
            subject_id="user-1",
        )
        restricted_decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.USER,
            subject_id="user-1",
            document_acl=acl,
        )

        assert default_decision.is_allowed() is True
        assert default_decision.matched_rule_id == PUBLIC_READ_RULE_ID
        assert restricted_decision.is_denied() is True

    def test_denies_anonymous_users_from_reading(self):
        service = AclService()
        acl = restrict_document_read(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="readers",
        )

        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ANONYMOUS,
            document_acl=acl,
        )

        assert decision.is_denied() is True


class TestRestrictDocumentDiscuss:
    """restrict_document_discuss가 지정한 대상에게만 토론 규칙을 부여하는지 확인한다."""

    def test_returns_document_acl_with_single_discuss_rule(self):
        acl = restrict_document_discuss(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="discussants",
        )

        assert acl.document_id == "doc-1"
        rules = acl.rules()
        assert len(rules) == 1
        rule = rules[0]
        assert rule.id == DOCUMENT_DISCUSS_RESTRICTION_RULE_ID
        assert rule.permission is Permission.DISCUSS
        assert rule.subject_type is SubjectType.GROUP
        assert rule.subject_id == "discussants"
        assert rule.is_allow() is True


class TestRestrictDocumentDiscussWithAclService:
    """제한된 문서 ACL이 AclService 검사에서 실제로 토론을 제한하는지 확인한다."""

    def test_allows_the_designated_group_to_discuss(self):
        service = AclService()
        acl = restrict_document_discuss(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="discussants",
        )

        decision = service.check(
            permission=Permission.DISCUSS,
            subject_type=SubjectType.GROUP,
            subject_id="discussants",
            document_acl=acl,
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == DOCUMENT_DISCUSS_RESTRICTION_RULE_ID

    def test_denies_a_different_group_from_discussing(self):
        service = AclService()
        acl = restrict_document_discuss(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="discussants",
        )

        decision = service.check(
            permission=Permission.DISCUSS,
            subject_type=SubjectType.GROUP,
            subject_id="visitors",
            document_acl=acl,
        )

        assert decision.is_denied() is True

    def test_denies_anonymous_users_from_discussing(self):
        service = AclService()
        acl = restrict_document_discuss(
            document_id="doc-1",
            subject_type=SubjectType.GROUP,
            subject_id="discussants",
        )

        decision = service.check(
            permission=Permission.DISCUSS,
            subject_type=SubjectType.ANONYMOUS,
            document_acl=acl,
        )

        assert decision.is_denied() is True

    def test_discuss_is_denied_by_default_without_document_acl(self):
        service = AclService(namespace_defaults=build_default_namespace_acl_defaults())

        decision = service.check(
            permission=Permission.DISCUSS,
            subject_type=SubjectType.USER,
            subject_id="user-1",
        )

        assert decision.is_denied() is True
