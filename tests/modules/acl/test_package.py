"""acl 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.acl
from modules.acl.rule import Rule


def test_acl_package_is_importable():
    assert modules.acl.__doc__ == "ACL module package."


def test_acl_package_exports_permission():
    # 0152에서 Permission 열거형이 추가되었으므로 export에 포함되어야 한다.
    assert "Permission" in modules.acl.__all__


def test_acl_package_exports_rule():
    # 0153에서 Rule 모델이 추가되었으므로 export에 포함되어야 한다.
    assert modules.acl.__all__ == [
        "Permission",
        "Rule",
        "SubjectType",
        "Effect",
        "EmptyRuleIdError",
        "MissingSubjectIdError",
    ]
    assert modules.acl.Rule is Rule
