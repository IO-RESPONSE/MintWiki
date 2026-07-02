"""DiscussionService와 협력 객체(저장소, 감사 기록기, 최근 활동 서비스)를
하나로 묶어 실제 시나리오를 끝까지 실행하는 통합 테스트.

개별 유닛 테스트(test_service.py 등)는 서비스 메서드 하나씩을 독립적으로
검증하지만, 이 파일은 하나의 DiscussionService 인스턴스를 여러 단계에
걸쳐 호출하면서 저장소/감사 기록기/최근 활동 서비스가 서로 일관된 결과를
내는지를 확인한다.
"""
import pytest

from modules.discussion.audit_event import DiscussionAuditAction
from modules.discussion.audit_recorder import DiscussionAuditRecorder
from modules.discussion.recent_activity_service import DiscussionRecentActivityService
from modules.discussion.repository import InMemoryDiscussionRepository
from modules.discussion.service import DiscussionService


@pytest.mark.asyncio
async def test_full_thread_lifecycle_stays_consistent_across_repository_and_audit_recorder():
    """스레드 생성, 댓글 추가, 일시정지/재개/닫기, 댓글 숨김을 서비스로 순서대로
    수행했을 때 저장소와 감사 기록기가 서로 일치하는 최종 상태를 갖는다."""
    repository = InMemoryDiscussionRepository()
    audit_recorder = DiscussionAuditRecorder()
    service = DiscussionService(repository, audit_recorder=audit_recorder)

    thread = await service.create_thread(
        document_id="doc1", title="제목", created_by="user1"
    )
    comment1 = await service.add_comment(
        thread_id=thread.id, body="첫 번째 댓글", created_by="user2"
    )
    comment2 = await service.add_comment(
        thread_id=thread.id, body="두 번째 댓글", created_by="user3"
    )
    await service.pause_thread(thread.id)
    await service.reopen_thread(thread.id)
    await service.close_thread(thread.id)
    hidden = await service.hide_comment(comment2.id, actor_id="moderator1")

    stored_thread = await repository.get_thread(thread.id)
    assert stored_thread.status == "closed"
    assert stored_thread.closed_at is not None

    stored_comments = await repository.list_comments_by_thread_id(thread.id)
    assert [c.id for c in stored_comments] == [comment1.id, comment2.id]
    assert stored_comments[0].is_hidden is False
    assert stored_comments[1].is_hidden is True
    assert stored_comments[1].hidden_at == hidden.hidden_at

    # 서비스는 스레드 생성과 댓글 숨김만 감사 이벤트로 남긴다(README에 문서화된
    # 부분 커버리지). 일시정지/재개/닫기/댓글 추가는 이벤트를 남기지 않는다.
    actions = [event.action for event in audit_recorder.events()]
    assert actions == [
        DiscussionAuditAction.THREAD_CREATED,
        DiscussionAuditAction.COMMENT_HIDDEN,
    ]


@pytest.mark.asyncio
async def test_recent_activity_service_reflects_actions_performed_through_service():
    """DiscussionService가 기록한 감사 이벤트를 같은 audit_recorder를 공유하는
    DiscussionRecentActivityService로 조회하면 최신순으로 일관되게 노출된다."""
    repository = InMemoryDiscussionRepository()
    audit_recorder = DiscussionAuditRecorder()
    service = DiscussionService(repository, audit_recorder=audit_recorder)
    recent_activity_service = DiscussionRecentActivityService(audit_recorder)

    thread = await service.create_thread(
        document_id="doc1", title="제목", created_by="user1"
    )
    comment = await service.add_comment(
        thread_id=thread.id, body="본문", created_by="user2"
    )
    await service.hide_comment(comment.id, actor_id="moderator1")

    activities = recent_activity_service.list_recent_activities(thread_id=thread.id)

    assert [a.action for a in activities] == [
        DiscussionAuditAction.COMMENT_HIDDEN,
        DiscussionAuditAction.THREAD_CREATED,
    ]
    assert activities[0].comment_id == comment.id
    assert activities[0].actor_id == "moderator1"
    assert activities[0].summary == "댓글이 숨김 처리되었습니다"
    assert activities[1].thread_id == thread.id
    assert activities[1].actor_id == "user1"
    assert activities[1].summary == "새 토론 스레드가 생성되었습니다"


@pytest.mark.asyncio
async def test_recent_activity_service_filters_out_other_threads_created_through_service():
    """여러 스레드를 서비스로 만들었을 때 최근 활동 서비스는 thread_id로
    올바르게 걸러낸다."""
    repository = InMemoryDiscussionRepository()
    audit_recorder = DiscussionAuditRecorder()
    service = DiscussionService(repository, audit_recorder=audit_recorder)
    recent_activity_service = DiscussionRecentActivityService(audit_recorder)

    thread1 = await service.create_thread(
        document_id="doc1", title="첫 번째", created_by="user1"
    )
    thread2 = await service.create_thread(
        document_id="doc1", title="두 번째", created_by="user1"
    )

    activities = recent_activity_service.list_recent_activities(thread_id=thread2.id)

    assert len(activities) == 1
    assert activities[0].thread_id == thread2.id
    assert activities[0].action is DiscussionAuditAction.THREAD_CREATED
    assert all(a.thread_id != thread1.id for a in activities)


@pytest.mark.asyncio
async def test_hidden_comment_body_stays_readable_via_moderator_view_after_full_lifecycle():
    """스레드를 닫은 뒤에도 숨긴 댓글의 본문은 모더레이터 뷰에서 그대로
    보이고, 일반 뷰에서는 계속 감춰진다."""
    repository = InMemoryDiscussionRepository()
    service = DiscussionService(repository, audit_recorder=DiscussionAuditRecorder())
    thread = await service.create_thread(
        document_id="doc1", title="제목", created_by="user1"
    )
    comment = await service.add_comment(
        thread_id=thread.id, body="모더레이터만 볼 수 있어야 할 본문", created_by="user2"
    )
    await service.close_thread(thread.id)
    await service.hide_comment(comment.id, actor_id="moderator1")

    stored_comments = await service.list_comments_by_thread_id(thread.id)
    moderator_view = stored_comments[0].to_moderator_view()
    public_view = stored_comments[0].to_public_view()

    assert moderator_view["body"] == "모더레이터만 볼 수 있어야 할 본문"
    assert public_view["body"] is None
    assert public_view["is_hidden"] is True
