"""user 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.user


def test_user_package_is_importable():
    assert modules.user.__doc__ == "User module package."


def test_user_package_exports_domain_model():
    assert modules.user.__all__ == [
        "User",
        "EmptyUsernameError",
        "AnonymousIdentity",
        "IpIdentity",
        "InvalidIpAddressError",
        "Group",
        "EmptyGroupNameError",
        "UserRepository",
        "InMemoryUserRepository",
        "PasswordHasher",
        "Session",
        "EmptySessionIdError",
        "EmptyUserIdError",
    ]
    assert modules.user.User is not None
    assert modules.user.EmptyUsernameError is not None
    assert modules.user.AnonymousIdentity is not None
    assert modules.user.IpIdentity is not None
    assert modules.user.InvalidIpAddressError is not None
    assert modules.user.Group is not None
    assert modules.user.EmptyGroupNameError is not None
    assert modules.user.UserRepository is not None
    assert modules.user.InMemoryUserRepository is not None
    assert modules.user.PasswordHasher is not None
    assert modules.user.Session is not None
    assert modules.user.EmptySessionIdError is not None
    assert modules.user.EmptyUserIdError is not None
