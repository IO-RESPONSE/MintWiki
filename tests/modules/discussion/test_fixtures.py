"""토론 픽스처 로더와 픽스처 형식을 검증한다."""
import pytest

from modules.discussion.audit_event import DiscussionAuditEvent
from modules.discussion.comment import DiscussionComment
from modules.discussion.fixtures import DiscussionFixture, DiscussionFixtureLoader
from modules.discussion.thread import DiscussionThread


class TestDiscussionFixtureLoaderLoadAll:
    """load_all이 반환하는 픽스처 목록의 형식을 검증한다."""

    def test_loads_all_fixtures(self):
        fixtures = DiscussionFixtureLoader.load_all()
        assert len(fixtures) > 0

    def test_returns_list_of_discussion_fixtures(self):
        fixtures = DiscussionFixtureLoader.load_all()
        assert all(isinstance(f, DiscussionFixture) for f in fixtures)

    def test_fixture_names_are_unique(self):
        fixtures = DiscussionFixtureLoader.load_all()
        names = [f.name for f in fixtures]
        assert len(names) == len(set(names))

    def test_each_fixture_has_a_thread(self):
        fixtures = DiscussionFixtureLoader.load_all()
        for fixture in fixtures:
            assert fixture.name
            assert isinstance(fixture.thread, DiscussionThread)

    def test_each_fixture_comment_belongs_to_its_thread(self):
        fixtures = DiscussionFixtureLoader.load_all()
        for fixture in fixtures:
            assert all(isinstance(c, DiscussionComment) for c in fixture.comments)
            assert all(c.thread_id == fixture.thread.id for c in fixture.comments)

    def test_each_fixture_audit_event_references_its_thread(self):
        fixtures = DiscussionFixtureLoader.load_all()
        for fixture in fixtures:
            assert all(
                isinstance(e, DiscussionAuditEvent) for e in fixture.audit_events
            )
            assert all(
                e.thread_id == fixture.thread.id for e in fixture.audit_events
            )

    def test_each_fixture_has_a_thread_created_audit_event(self):
        fixtures = DiscussionFixtureLoader.load_all()
        for fixture in fixtures:
            assert any(e.is_thread_created() for e in fixture.audit_events)


class TestDiscussionFixtureLoaderLoadByName:
    """load_by_name이 이름으로 픽스처를 조회하는 동작을 검증한다."""

    def test_loads_known_fixture(self):
        fixture = DiscussionFixtureLoader.load_by_name(
            "open_thread_with_no_comments"
        )
        assert fixture.name == "open_thread_with_no_comments"

    def test_raises_error_for_unknown_fixture(self):
        with pytest.raises(ValueError, match="Unknown fixture"):
            DiscussionFixtureLoader.load_by_name("nonexistent_fixture")


class TestDiscussionFixtureScenarios:
    """개별 시나리오 픽스처의 세부 내용을 검증한다."""

    def test_open_thread_with_no_comments_has_no_comments(self):
        fixture = DiscussionFixtureLoader.load_by_name(
            "open_thread_with_no_comments"
        )
        assert fixture.thread.is_open()
        assert fixture.comments == []

    def test_closed_thread_with_comments_is_closed(self):
        fixture = DiscussionFixtureLoader.load_by_name(
            "closed_thread_with_comments"
        )
        assert fixture.thread.status == "closed"
        assert len(fixture.comments) > 0

    def test_paused_thread_with_comments_is_paused(self):
        fixture = DiscussionFixtureLoader.load_by_name(
            "paused_thread_with_comments"
        )
        assert fixture.thread.is_paused()
        assert len(fixture.comments) > 0

    def test_thread_with_hidden_comment_has_hidden_comment(self):
        fixture = DiscussionFixtureLoader.load_by_name(
            "thread_with_hidden_comment"
        )
        assert any(c.is_hidden for c in fixture.comments)

    def test_thread_with_multiple_hidden_comments_has_mixed_visibility(self):
        fixture = DiscussionFixtureLoader.load_by_name(
            "thread_with_multiple_hidden_comments"
        )
        hidden = [c for c in fixture.comments if c.is_hidden]
        visible = [c for c in fixture.comments if not c.is_hidden]
        assert len(hidden) > 1
        assert len(visible) > 0
