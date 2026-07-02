"""사용자 그룹 소속 여부와 ACL GROUP 대상 규칙의 상호작용을 검증한다."""
from typing import Iterable, Optional

from modules.acl.decision import Decision
from modules.acl.document_acl import DocumentAcl
from modules.acl.namespace_defaults import DEFAULT_NAMESPACE
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.service import AclService
from modules.user.group import Group


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


def _check_for_member_groups(
    service: AclService,
    permission: Permission,
    user_id: str,
    groups: Iterable[Group],
    document_acl: Optional[DocumentAcl] = None,
    namespace: str = DEFAULT_NAMESPACE,
) -> Decision:
    """사용자가 실제로 소속된 그룹에 한해서만 GROUP 규칙을 검사한다.

    AclService.check는 subject_id로 어떤 그룹을 검사할지 그대로 전달받을
    뿐 소속 여부는 판단하지 않으므로, 호출자가 Group.has_member로 소속을
    먼저 확인한 뒤에만 해당 그룹 id를 전달해야 한다는 사용 계약을
    재현하는 테스트 전용 헬퍼다.
    """
    for group in groups:
        if not group.has_member(user_id):
            continue
        decision = service.check(
            permission=permission,
            subject_type=SubjectType.GROUP,
            subject_id=group.id,
            document_acl=document_acl,
            namespace=namespace,
        )
        if decision.matched_rule_id is not None:
            return decision

    return service.check(
        permission=permission,
        subject_type=SubjectType.ALL,
        document_acl=document_acl,
        namespace=namespace,
    )


class TestGroupMemberMatchesGroupRule:
    """그룹에 소속된 사용자가 해당 그룹 대상 규칙의 effect를 적용받는지 확인한다."""

    def test_group_member_is_allowed_by_group_allow_rule(self):
        group = Group(id="group-1", name="editors", member_ids=["user-1"])
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-edit-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group.id,
                    effect=Effect.ALLOW,
                )
            ],
        )

        decision = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group], document_acl
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "group-edit-allow"

    def test_group_member_is_denied_by_group_deny_rule(self):
        group = Group(id="group-2", name="blocked", member_ids=["user-1"])
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-edit-deny",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group.id,
                    effect=Effect.DENY,
                )
            ],
        )

        decision = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group], document_acl
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id == "group-edit-deny"

    def test_non_member_does_not_match_group_rule(self):
        group = Group(id="group-3", name="editors", member_ids=["user-1"])
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-edit-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group.id,
                    effect=Effect.ALLOW,
                )
            ],
        )

        decision = _check_for_member_groups(
            service, Permission.EDIT, "user-2", [group], document_acl
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id is None


class TestMembershipChangesAffectDecision:
    """add_member/remove_member로 소속이 바뀌면 검사 결과도 함께 바뀌는지 확인한다."""

    def test_adding_member_grants_access_previously_denied(self):
        group = Group(id="group-4", name="editors")
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-edit-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group.id,
                    effect=Effect.ALLOW,
                )
            ],
        )

        before = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group], document_acl
        )
        group.add_member("user-1")
        after = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group], document_acl
        )

        assert before.is_denied() is True
        assert after.is_allowed() is True

    def test_removing_member_revokes_previously_allowed_access(self):
        group = Group(id="group-5", name="editors", member_ids=["user-1"])
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-edit-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group.id,
                    effect=Effect.ALLOW,
                )
            ],
        )

        before = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group], document_acl
        )
        group.remove_member("user-1")
        after = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group], document_acl
        )

        assert before.is_allowed() is True
        assert after.is_denied() is True


class TestUserInMultipleGroups:
    """사용자가 여러 그룹에 속할 때 실제로 소속된 그룹의 규칙만 순서대로 검사되는지 확인한다."""

    def test_first_matching_group_among_multiple_memberships_wins(self):
        group_a = Group(id="group-a", name="reviewers", member_ids=["user-1"])
        group_b = Group(id="group-b", name="editors", member_ids=["user-1"])
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-a-deny",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group_a.id,
                    effect=Effect.DENY,
                ),
                _rule(
                    "group-b-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group_b.id,
                    effect=Effect.ALLOW,
                ),
            ],
        )

        decision = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group_a, group_b], document_acl
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id == "group-a-deny"

    def test_only_matching_group_membership_grants_access(self):
        group_a = Group(id="group-a", name="reviewers", member_ids=["user-2"])
        group_b = Group(id="group-b", name="editors", member_ids=["user-1"])
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-a-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group_a.id,
                    effect=Effect.ALLOW,
                ),
                _rule(
                    "group-b-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group_b.id,
                    effect=Effect.ALLOW,
                ),
            ],
        )

        decision = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group_a, group_b], document_acl
        )

        assert decision.is_allowed() is True
        assert decision.matched_rule_id == "group-b-allow"

    def test_user_in_no_relevant_group_falls_back_to_all_rule(self):
        group_a = Group(id="group-a", name="reviewers", member_ids=["user-2"])
        service = AclService()
        document_acl = DocumentAcl(
            document_id="doc-1",
            rules=[
                _rule(
                    "group-a-allow",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.GROUP,
                    subject_id=group_a.id,
                    effect=Effect.ALLOW,
                ),
                _rule(
                    "fallback-all-deny",
                    permission=Permission.EDIT,
                    subject_type=SubjectType.ALL,
                    effect=Effect.DENY,
                ),
            ],
        )

        decision = _check_for_member_groups(
            service, Permission.EDIT, "user-1", [group_a], document_acl
        )

        assert decision.is_denied() is True
        assert decision.matched_rule_id == "fallback-all-deny"
