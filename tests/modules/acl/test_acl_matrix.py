"""문서 ACL 규칙에 대한 대상×권한 전체 조합의 기본 매트릭스를 검증한다."""
import pytest

from modules.acl.document_acl import DocumentAcl
from modules.acl.permission import Permission
from modules.acl.rule import Effect, Rule, SubjectType
from modules.acl.service import AclService

READ_ALL_ALLOW = "read-all-allow"
EDIT_OWNER_ALLOW = "edit-owner-allow"
EDIT_GROUP_ALLOW = "edit-group-allow"
EDIT_ALL_DENY = "edit-all-deny"

# (레이블, 대상 종류, 대상 id) - 매트릭스의 행이 되는 대상 목록.
SUBJECTS = [
    ("all", SubjectType.ALL, None),
    ("anonymous", SubjectType.ANONYMOUS, None),
    ("owner-user", SubjectType.USER, "user-1"),
    ("other-user", SubjectType.USER, "user-2"),
    ("editors-group", SubjectType.GROUP, "editors"),
    ("reviewers-group", SubjectType.GROUP, "reviewers"),
]

_SUBJECTS_BY_LABEL = {label: (subject_type, subject_id) for label, subject_type, subject_id in SUBJECTS}

# (대상 레이블, 권한, 기대 허용 여부, 기대 매칭 규칙 id) - 매트릭스의 각 셀.
MATRIX = [
    ("all", Permission.READ, True, READ_ALL_ALLOW),
    ("anonymous", Permission.READ, True, READ_ALL_ALLOW),
    ("owner-user", Permission.READ, True, READ_ALL_ALLOW),
    ("other-user", Permission.READ, True, READ_ALL_ALLOW),
    ("editors-group", Permission.READ, True, READ_ALL_ALLOW),
    ("reviewers-group", Permission.READ, True, READ_ALL_ALLOW),
    ("all", Permission.EDIT, False, EDIT_ALL_DENY),
    ("anonymous", Permission.EDIT, False, EDIT_ALL_DENY),
    ("owner-user", Permission.EDIT, True, EDIT_OWNER_ALLOW),
    ("other-user", Permission.EDIT, False, EDIT_ALL_DENY),
    ("editors-group", Permission.EDIT, True, EDIT_GROUP_ALLOW),
    ("reviewers-group", Permission.EDIT, False, EDIT_ALL_DENY),
    *[
        (label, permission, False, None)
        for label, _, _ in SUBJECTS
        for permission in (
            Permission.DISCUSS,
            Permission.MOVE,
            Permission.DELETE,
            Permission.ADMIN,
        )
    ],
]


def _build_document_acl() -> DocumentAcl:
    """읽기는 전체 허용, 편집은 소유자(user-1)와 editors 그룹만 허용하는 문서 ACL을 만든다."""
    return DocumentAcl(
        document_id="matrix-doc",
        rules=[
            Rule(
                id=READ_ALL_ALLOW,
                subject_type=SubjectType.ALL,
                permission=Permission.READ,
                effect=Effect.ALLOW,
            ),
            Rule(
                id=EDIT_OWNER_ALLOW,
                subject_type=SubjectType.USER,
                subject_id="user-1",
                permission=Permission.EDIT,
                effect=Effect.ALLOW,
            ),
            Rule(
                id=EDIT_GROUP_ALLOW,
                subject_type=SubjectType.GROUP,
                subject_id="editors",
                permission=Permission.EDIT,
                effect=Effect.ALLOW,
            ),
            Rule(
                id=EDIT_ALL_DENY,
                subject_type=SubjectType.ALL,
                permission=Permission.EDIT,
                effect=Effect.DENY,
            ),
        ],
    )


class TestAclMatrixBasicGrid:
    """전체 대상 종류 × 권한 종류 조합에 대한 기본 허용/거부 매트릭스를 검증한다."""

    @pytest.mark.parametrize("label, permission, expected_allowed, expected_matched_rule_id", MATRIX)
    def test_decision_matches_expected_cell(
        self, label, permission, expected_allowed, expected_matched_rule_id
    ):
        subject_type, subject_id = _SUBJECTS_BY_LABEL[label]
        service = AclService()
        document_acl = _build_document_acl()

        decision = service.check(
            permission=permission,
            subject_type=subject_type,
            subject_id=subject_id,
            document_acl=document_acl,
        )

        assert decision.is_allowed() is expected_allowed
        assert decision.matched_rule_id == expected_matched_rule_id

    def test_matrix_covers_every_subject_and_permission_combination(self):
        expected_combinations = {
            (label, permission) for label, _, _ in SUBJECTS for permission in Permission
        }
        actual_combinations = {(label, permission) for label, permission, _, _ in MATRIX}

        assert actual_combinations == expected_combinations
