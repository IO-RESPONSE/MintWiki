"""Permission 열거형 테스트."""
from modules.acl.permission import Permission


class TestPermissionMembers:
    """Permission 열거형이 정의해야 할 권한 종류를 검증한다."""

    def test_has_read_permission(self):
        """읽기 권한이 정의되어 있다."""
        assert Permission.READ.value == "read"

    def test_has_edit_permission(self):
        """편집 권한이 정의되어 있다."""
        assert Permission.EDIT.value == "edit"

    def test_has_discuss_permission(self):
        """토론 권한이 정의되어 있다."""
        assert Permission.DISCUSS.value == "discuss"

    def test_has_move_permission(self):
        """이동 권한이 정의되어 있다."""
        assert Permission.MOVE.value == "move"

    def test_has_delete_permission(self):
        """삭제 권한이 정의되어 있다."""
        assert Permission.DELETE.value == "delete"

    def test_has_admin_permission(self):
        """관리자 권한이 정의되어 있다."""
        assert Permission.ADMIN.value == "admin"

    def test_permission_values_are_unique(self):
        """모든 권한 값은 서로 중복되지 않는다."""
        values = [permission.value for permission in Permission]
        assert len(values) == len(set(values))

    def test_permission_is_importable_from_acl_package(self):
        """acl 패키지 최상위에서 Permission을 임포트할 수 있다."""
        import modules.acl

        assert modules.acl.Permission is Permission
