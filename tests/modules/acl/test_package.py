"""acl 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.acl


def test_acl_package_is_importable():
    assert modules.acl.__doc__ == "ACL module package."


def test_acl_package_exports_are_empty_for_now():
    # 0152 이후 도메인 모델이 추가되기 전까지는 export가 없어야 한다.
    assert modules.acl.__all__ == []
