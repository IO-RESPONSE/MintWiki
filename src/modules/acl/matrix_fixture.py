"""ACL 권한 매트릭스 테스트 픽스처 로더."""
from typing import List, NamedTuple, Optional

from modules.acl.document_acl import DocumentAcl
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType


class AclMatrixCase(NamedTuple):
    """
    ACL 매트릭스 픽스처의 한 행(row).

    같은 픽스처의 규칙 집합(AclMatrixFixture.rules) 아래에서 특정 대상이
    특정 권한에 대해 허용되는지(expected_allowed)와, 그 근거가 된 규칙
    id(expected_matched_rule_id)를 표현한다. 일치하는 규칙이 없을 것으로
    예상되면 expected_matched_rule_id는 None으로 둔다.
    """

    subject_type: SubjectType
    permission: Permission
    expected_allowed: bool
    subject_id: Optional[str] = None
    expected_matched_rule_id: Optional[str] = None


class AclMatrixFixture(NamedTuple):
    """
    하나의 규칙 집합(rules)과 그 규칙 집합에 대해 검사할 여러
    케이스(cases)를 묶은 ACL 매트릭스 픽스처.
    """

    name: str
    rules: List[Rule]
    cases: List[AclMatrixCase]

    def document_acl(self, document_id: str = "fixture-doc") -> DocumentAcl:
        """픽스처의 규칙으로 DocumentAcl을 생성한다."""
        return DocumentAcl(document_id=document_id, rules=self.rules)


class AclMatrixFixtureLoader:
    """ACL 매트릭스 테스트 픽스처 로더."""

    @staticmethod
    def load_all() -> List[AclMatrixFixture]:
        """
        모든 ACL 매트릭스 픽스처를 로드한다.

        Returns:
            ACL 매트릭스 픽스처 목록
        """
        return [
            AclMatrixFixtureLoader._public_read_only(),
            AclMatrixFixtureLoader._owner_user_allowed_others_denied(),
            AclMatrixFixtureLoader._group_edit_with_anonymous_read_denied(),
            AclMatrixFixtureLoader._full_permission_grid_for_all_subjects(),
            AclMatrixFixtureLoader._first_match_wins_regardless_of_specificity(),
            AclMatrixFixtureLoader._no_matching_rule_denies_by_default(),
        ]

    @staticmethod
    def load_by_name(name: str) -> AclMatrixFixture:
        """
        이름으로 특정 ACL 매트릭스 픽스처를 로드한다.

        Args:
            name: 픽스처 이름

        Returns:
            ACL 매트릭스 픽스처

        Raises:
            ValueError: 해당 이름의 픽스처가 없음
        """
        fixtures = {f.name: f for f in AclMatrixFixtureLoader.load_all()}
        if name not in fixtures:
            raise ValueError(f"Unknown fixture: {name}")
        return fixtures[name]

    @staticmethod
    def _public_read_only() -> AclMatrixFixture:
        """모든 대상에게 read만 허용되고 나머지 권한은 거부되는 매트릭스."""
        return AclMatrixFixture(
            name="public_read_only",
            rules=[
                Rule(
                    id="all-read-allow",
                    subject_type=SubjectType.ALL,
                    permission=Permission.READ,
                    effect=Effect.ALLOW,
                ),
            ],
            cases=[
                AclMatrixCase(
                    SubjectType.ALL,
                    Permission.READ,
                    True,
                    expected_matched_rule_id="all-read-allow",
                ),
                AclMatrixCase(
                    SubjectType.ANONYMOUS,
                    Permission.READ,
                    True,
                    expected_matched_rule_id="all-read-allow",
                ),
                AclMatrixCase(
                    SubjectType.USER, Permission.EDIT, False, subject_id="user-1"
                ),
                AclMatrixCase(SubjectType.ALL, Permission.DELETE, False),
            ],
        )

    @staticmethod
    def _owner_user_allowed_others_denied() -> AclMatrixFixture:
        """특정 사용자에게만 edit을 허용하고 그 외 대상은 거부되는 매트릭스."""
        return AclMatrixFixture(
            name="owner_user_allowed_others_denied",
            rules=[
                Rule(
                    id="owner-edit-allow",
                    subject_type=SubjectType.USER,
                    subject_id="user-1",
                    permission=Permission.EDIT,
                    effect=Effect.ALLOW,
                ),
                Rule(
                    id="all-edit-deny",
                    subject_type=SubjectType.ALL,
                    permission=Permission.EDIT,
                    effect=Effect.DENY,
                ),
            ],
            cases=[
                AclMatrixCase(
                    SubjectType.USER,
                    Permission.EDIT,
                    True,
                    subject_id="user-1",
                    expected_matched_rule_id="owner-edit-allow",
                ),
                AclMatrixCase(
                    SubjectType.USER,
                    Permission.EDIT,
                    False,
                    subject_id="user-2",
                    expected_matched_rule_id="all-edit-deny",
                ),
                AclMatrixCase(
                    SubjectType.ANONYMOUS,
                    Permission.EDIT,
                    False,
                    expected_matched_rule_id="all-edit-deny",
                ),
            ],
        )

    @staticmethod
    def _group_edit_with_anonymous_read_denied() -> AclMatrixFixture:
        """그룹에는 edit을 허용하고 익명 사용자에게는 read를 거부하는 매트릭스."""
        return AclMatrixFixture(
            name="group_edit_with_anonymous_read_denied",
            rules=[
                Rule(
                    id="group-edit-allow",
                    subject_type=SubjectType.GROUP,
                    subject_id="editors",
                    permission=Permission.EDIT,
                    effect=Effect.ALLOW,
                ),
                Rule(
                    id="anonymous-read-deny",
                    subject_type=SubjectType.ANONYMOUS,
                    permission=Permission.READ,
                    effect=Effect.DENY,
                ),
            ],
            cases=[
                AclMatrixCase(
                    SubjectType.GROUP,
                    Permission.EDIT,
                    True,
                    subject_id="editors",
                    expected_matched_rule_id="group-edit-allow",
                ),
                AclMatrixCase(
                    SubjectType.GROUP,
                    Permission.EDIT,
                    False,
                    subject_id="reviewers",
                ),
                AclMatrixCase(
                    SubjectType.ANONYMOUS,
                    Permission.READ,
                    False,
                    expected_matched_rule_id="anonymous-read-deny",
                ),
                AclMatrixCase(
                    SubjectType.USER, Permission.READ, False, subject_id="user-1"
                ),
            ],
        )

    @staticmethod
    def _full_permission_grid_for_all_subjects() -> AclMatrixFixture:
        """모든 권한 종류에 대해 서로 다른 effect를 조합한 매트릭스."""
        return AclMatrixFixture(
            name="full_permission_grid_for_all_subjects",
            rules=[
                Rule(
                    id="read-allow",
                    subject_type=SubjectType.ALL,
                    permission=Permission.READ,
                    effect=Effect.ALLOW,
                ),
                Rule(
                    id="edit-allow",
                    subject_type=SubjectType.ALL,
                    permission=Permission.EDIT,
                    effect=Effect.ALLOW,
                ),
                Rule(
                    id="discuss-allow",
                    subject_type=SubjectType.ALL,
                    permission=Permission.DISCUSS,
                    effect=Effect.ALLOW,
                ),
                Rule(
                    id="move-deny",
                    subject_type=SubjectType.ALL,
                    permission=Permission.MOVE,
                    effect=Effect.DENY,
                ),
                Rule(
                    id="delete-deny",
                    subject_type=SubjectType.ALL,
                    permission=Permission.DELETE,
                    effect=Effect.DENY,
                ),
                Rule(
                    id="admin-deny",
                    subject_type=SubjectType.ALL,
                    permission=Permission.ADMIN,
                    effect=Effect.DENY,
                ),
            ],
            cases=[
                AclMatrixCase(
                    SubjectType.ALL,
                    Permission.READ,
                    True,
                    expected_matched_rule_id="read-allow",
                ),
                AclMatrixCase(
                    SubjectType.ALL,
                    Permission.EDIT,
                    True,
                    expected_matched_rule_id="edit-allow",
                ),
                AclMatrixCase(
                    SubjectType.ALL,
                    Permission.DISCUSS,
                    True,
                    expected_matched_rule_id="discuss-allow",
                ),
                AclMatrixCase(
                    SubjectType.ALL,
                    Permission.MOVE,
                    False,
                    expected_matched_rule_id="move-deny",
                ),
                AclMatrixCase(
                    SubjectType.ALL,
                    Permission.DELETE,
                    False,
                    expected_matched_rule_id="delete-deny",
                ),
                AclMatrixCase(
                    SubjectType.ALL,
                    Permission.ADMIN,
                    False,
                    expected_matched_rule_id="admin-deny",
                ),
            ],
        )

    @staticmethod
    def _first_match_wins_regardless_of_specificity() -> AclMatrixFixture:
        """등록 순서가 우선이며 대상의 구체성과는 무관함을 보여주는 매트릭스."""
        return AclMatrixFixture(
            name="first_match_wins_regardless_of_specificity",
            rules=[
                Rule(
                    id="all-deny",
                    subject_type=SubjectType.ALL,
                    permission=Permission.READ,
                    effect=Effect.DENY,
                ),
                Rule(
                    id="user-allow",
                    subject_type=SubjectType.USER,
                    subject_id="user-1",
                    permission=Permission.READ,
                    effect=Effect.ALLOW,
                ),
            ],
            cases=[
                AclMatrixCase(
                    SubjectType.USER,
                    Permission.READ,
                    False,
                    subject_id="user-1",
                    expected_matched_rule_id="all-deny",
                ),
                AclMatrixCase(
                    SubjectType.USER,
                    Permission.READ,
                    False,
                    subject_id="user-2",
                    expected_matched_rule_id="all-deny",
                ),
                AclMatrixCase(
                    SubjectType.ANONYMOUS,
                    Permission.READ,
                    False,
                    expected_matched_rule_id="all-deny",
                ),
            ],
        )

    @staticmethod
    def _no_matching_rule_denies_by_default() -> AclMatrixFixture:
        """일치하는 규칙이 없는 대상/권한 조합은 기본적으로 거부되는 매트릭스."""
        return AclMatrixFixture(
            name="no_matching_rule_denies_by_default",
            rules=[
                Rule(
                    id="edit-only-allow",
                    subject_type=SubjectType.ALL,
                    permission=Permission.EDIT,
                    effect=Effect.ALLOW,
                ),
            ],
            cases=[
                AclMatrixCase(
                    SubjectType.ALL,
                    Permission.EDIT,
                    True,
                    expected_matched_rule_id="edit-only-allow",
                ),
                AclMatrixCase(SubjectType.ALL, Permission.READ, False),
                AclMatrixCase(
                    SubjectType.USER,
                    Permission.DELETE,
                    False,
                    subject_id="user-9",
                ),
            ],
        )


__all__ = ["AclMatrixCase", "AclMatrixFixture", "AclMatrixFixtureLoader"]
