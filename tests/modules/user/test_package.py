"""user 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.user


def test_user_package_is_importable():
    assert modules.user.__doc__ == "User module package."


def test_user_package_exports_domain_model():
    assert modules.user.__all__ == ["User", "EmptyUsernameError"]
    assert modules.user.User is not None
    assert modules.user.EmptyUsernameError is not None
