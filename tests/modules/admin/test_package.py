"""admin 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.admin


def test_admin_package_is_importable():
    """admin 패키지를 import할 수 있다."""
    assert modules.admin.__doc__ == "Admin module package."


def test_admin_package_exports():
    """__all__에 선언된 이름이 실제 모듈 속성으로 존재한다."""
    assert modules.admin.__all__ == []
    for name in modules.admin.__all__:
        assert hasattr(modules.admin, name)
