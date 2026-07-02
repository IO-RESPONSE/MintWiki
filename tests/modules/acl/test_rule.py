"""Rule 도메인 모델 테스트."""
from datetime import datetime, timedelta

import pytest

from modules.acl.permission import Permission
from modules.acl.rule import (
    Effect,
    EmptyRuleIdError,
    MissingSubjectIdError,
    Rule,
    SubjectType,
)


class TestRuleCreation:
    """Rule 생성 시의 검증 로직을 확인한다."""

    def test_creates_user_rule(self):
        rule = Rule(
            id="rule-1",
            subject_type=SubjectType.USER,
            permission=Permission.EDIT,
            effect=Effect.ALLOW,
            subject_id="user-1",
        )

        assert rule.id == "rule-1"
        assert rule.subject_type is SubjectType.USER
        assert rule.subject_id == "user-1"
        assert rule.permission is Permission.EDIT
        assert rule.effect is Effect.ALLOW

    def test_creates_group_rule(self):
        rule = Rule(
            id="rule-2",
            subject_type=SubjectType.GROUP,
            permission=Permission.READ,
            effect=Effect.DENY,
            subject_id="group-1",
        )

        assert rule.subject_type is SubjectType.GROUP
        assert rule.subject_id == "group-1"

    def test_creates_all_rule_without_subject_id(self):
        rule = Rule(
            id="rule-3",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
        )

        assert rule.subject_type is SubjectType.ALL
        assert rule.subject_id is None

    def test_creates_anonymous_rule_without_subject_id(self):
        rule = Rule(
            id="rule-4",
            subject_type=SubjectType.ANONYMOUS,
            permission=Permission.EDIT,
            effect=Effect.DENY,
        )

        assert rule.subject_type is SubjectType.ANONYMOUS
        assert rule.subject_id is None

    def test_raises_when_id_is_empty(self):
        with pytest.raises(EmptyRuleIdError):
            Rule(
                id="",
                subject_type=SubjectType.ALL,
                permission=Permission.READ,
                effect=Effect.ALLOW,
            )

    def test_raises_when_id_is_blank(self):
        with pytest.raises(EmptyRuleIdError):
            Rule(
                id="   ",
                subject_type=SubjectType.ALL,
                permission=Permission.READ,
                effect=Effect.ALLOW,
            )

    def test_raises_when_user_rule_has_no_subject_id(self):
        with pytest.raises(MissingSubjectIdError):
            Rule(
                id="rule-5",
                subject_type=SubjectType.USER,
                permission=Permission.READ,
                effect=Effect.ALLOW,
            )

    def test_raises_when_group_rule_has_no_subject_id(self):
        with pytest.raises(MissingSubjectIdError):
            Rule(
                id="rule-6",
                subject_type=SubjectType.GROUP,
                permission=Permission.READ,
                effect=Effect.ALLOW,
            )

    def test_defaults_expires_at_to_none(self):
        rule = Rule(
            id="rule-13",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
        )

        assert rule.expires_at is None

    def test_creates_rule_with_expires_at(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        rule = Rule(
            id="rule-14",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
            expires_at=expires_at,
        )

        assert rule.expires_at == expires_at


class TestRuleIsAllow:
    """is_allow 메서드가 effect에 따라 올바른 값을 반환하는지 확인한다."""

    def test_returns_true_for_allow_effect(self):
        rule = Rule(
            id="rule-7",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
        )

        assert rule.is_allow() is True

    def test_returns_false_for_deny_effect(self):
        rule = Rule(
            id="rule-8",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.DENY,
        )

        assert rule.is_allow() is False


class TestRuleAppliesTo:
    """applies_to 메서드가 대상 종류와 일치 여부를 올바르게 판단하는지 확인한다."""

    def test_all_rule_applies_to_any_subject(self):
        rule = Rule(
            id="rule-9",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
        )

        assert rule.applies_to(SubjectType.USER, "user-1") is True
        assert rule.applies_to(SubjectType.ANONYMOUS) is True

    def test_user_rule_applies_only_to_matching_user(self):
        rule = Rule(
            id="rule-10",
            subject_type=SubjectType.USER,
            permission=Permission.EDIT,
            effect=Effect.ALLOW,
            subject_id="user-1",
        )

        assert rule.applies_to(SubjectType.USER, "user-1") is True
        assert rule.applies_to(SubjectType.USER, "user-2") is False
        assert rule.applies_to(SubjectType.GROUP, "user-1") is False

    def test_group_rule_applies_only_to_matching_group(self):
        rule = Rule(
            id="rule-11",
            subject_type=SubjectType.GROUP,
            permission=Permission.EDIT,
            effect=Effect.ALLOW,
            subject_id="group-1",
        )

        assert rule.applies_to(SubjectType.GROUP, "group-1") is True
        assert rule.applies_to(SubjectType.GROUP, "group-2") is False

    def test_anonymous_rule_applies_only_to_anonymous(self):
        rule = Rule(
            id="rule-12",
            subject_type=SubjectType.ANONYMOUS,
            permission=Permission.READ,
            effect=Effect.ALLOW,
        )

        assert rule.applies_to(SubjectType.ANONYMOUS) is True
        assert rule.applies_to(SubjectType.USER, "user-1") is False


class TestRuleIsTemporary:
    """is_temporary 메서드가 expires_at 존재 여부에 따라 올바른 값을 반환하는지 확인한다."""

    def test_returns_false_when_expires_at_is_none(self):
        rule = Rule(
            id="rule-15",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
        )

        assert rule.is_temporary() is False

    def test_returns_true_when_expires_at_is_set(self):
        rule = Rule(
            id="rule-16",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
            expires_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert rule.is_temporary() is True


class TestRuleIsExpired:
    """is_expired 메서드가 만료 시각을 기준으로 올바른 값을 반환하는지 확인한다."""

    def test_returns_false_when_expires_at_is_none(self):
        rule = Rule(
            id="rule-17",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
        )

        assert rule.is_expired(datetime(2026, 1, 1, 0, 0, 0)) is False

    def test_returns_false_before_expiry(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        rule = Rule(
            id="rule-18",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
            expires_at=expires_at,
        )

        assert rule.is_expired(expires_at - timedelta(minutes=30)) is False

    def test_returns_true_after_expiry(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        rule = Rule(
            id="rule-19",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
            expires_at=expires_at,
        )

        assert rule.is_expired(expires_at + timedelta(seconds=1)) is True

    def test_returns_true_at_exact_expiry_time(self):
        expires_at = datetime(2026, 1, 1, 0, 0, 0)
        rule = Rule(
            id="rule-20",
            subject_type=SubjectType.ALL,
            permission=Permission.READ,
            effect=Effect.ALLOW,
            expires_at=expires_at,
        )

        assert rule.is_expired(expires_at) is True
