"""사용자 그룹 모델 테스트."""
import pytest
from modules.user.group import EmptyGroupNameError, Group


class TestGroupConstruction:
    """사용자 그룹 생성 테스트."""

    def test_creates_group_with_required_fields(self):
        """필수 필드로 그룹을 생성한다."""
        group = Group(id="group1", name="editors")
        assert group.id == "group1"
        assert group.name == "editors"
        assert group.member_ids == []

    def test_creates_group_with_member_ids(self):
        """소속 사용자 id 목록과 함께 그룹을 생성한다."""
        group = Group(id="group2", name="admins", member_ids=["user1", "user2"])
        assert group.member_ids == ["user1", "user2"]

    def test_preserves_unicode_group_name(self):
        """유니코드 그룹명을 그대로 보존한다."""
        group = Group(id="group3", name="관리자그룹")
        assert group.name == "관리자그룹"

    def test_copies_member_ids_to_avoid_aliasing(self):
        """전달된 member_ids 목록을 복사하여 외부 변경의 영향을 받지 않는다."""
        source = ["user1"]
        group = Group(id="group4", name="editors", member_ids=source)
        source.append("user2")
        assert group.member_ids == ["user1"]

    def test_rejects_empty_group_name(self):
        """빈 그룹명으로 그룹을 생성할 수 없다."""
        with pytest.raises(EmptyGroupNameError):
            Group(id="group5", name="")

    def test_rejects_whitespace_only_group_name(self):
        """공백만 있는 그룹명으로 그룹을 생성할 수 없다."""
        with pytest.raises(EmptyGroupNameError):
            Group(id="group6", name="   ")


class TestGroupMembership:
    """사용자 그룹 구성원 관리 테스트."""

    def test_has_member_returns_true_for_existing_member(self):
        """소속된 사용자에 대해 has_member가 True를 반환한다."""
        group = Group(id="group7", name="editors", member_ids=["user1"])
        assert group.has_member("user1") is True

    def test_has_member_returns_false_for_non_member(self):
        """소속되지 않은 사용자에 대해 has_member가 False를 반환한다."""
        group = Group(id="group8", name="editors")
        assert group.has_member("user1") is False

    def test_add_member_adds_user_to_group(self):
        """add_member로 사용자를 그룹에 추가한다."""
        group = Group(id="group9", name="editors")
        group.add_member("user1")
        assert group.has_member("user1") is True

    def test_add_member_does_not_duplicate_existing_member(self):
        """이미 소속된 사용자를 add_member로 추가해도 중복되지 않는다."""
        group = Group(id="group10", name="editors", member_ids=["user1"])
        group.add_member("user1")
        assert group.member_ids == ["user1"]

    def test_remove_member_removes_user_from_group(self):
        """remove_member로 사용자를 그룹에서 제외한다."""
        group = Group(id="group11", name="editors", member_ids=["user1"])
        group.remove_member("user1")
        assert group.has_member("user1") is False

    def test_remove_member_is_noop_for_non_member(self):
        """소속되지 않은 사용자를 remove_member로 제거해도 오류가 발생하지 않는다."""
        group = Group(id="group12", name="editors")
        group.remove_member("user1")
        assert group.member_ids == []
