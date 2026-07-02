"""user 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.user


def test_user_package_is_importable():
    assert modules.user.__doc__ == "User module package."


def test_user_package_exports_are_empty_for_now():
    # 0142에서 도메인 모델이 추가되기 전까지는 export가 없어야 한다.
    assert modules.user.__all__ == []
