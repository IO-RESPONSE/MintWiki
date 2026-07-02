"""discussion 패키지가 정상적으로 임포트되는지 확인한다."""
import modules.discussion


def test_discussion_package_is_importable():
    assert modules.discussion.__doc__ == "Discussion module package."


def test_discussion_package_exports_thread_model():
    assert modules.discussion.__all__ == [
        "DiscussionThread",
        "EmptyThreadIdError",
        "EmptyThreadDocumentIdError",
        "EmptyThreadTitleError",
        "EmptyThreadCreatedByError",
        "DiscussionComment",
        "EmptyCommentIdError",
        "EmptyCommentThreadIdError",
        "EmptyCommentBodyError",
        "EmptyCommentCreatedByError",
        "ThreadState",
        "DiscussionRepository",
        "DiscussionThreadNotFoundError",
        "InMemoryDiscussionRepository",
        "DiscussionService",
    ]
    assert modules.discussion.DiscussionThread is not None
    assert modules.discussion.EmptyThreadIdError is not None
    assert modules.discussion.EmptyThreadDocumentIdError is not None
    assert modules.discussion.EmptyThreadTitleError is not None
    assert modules.discussion.EmptyThreadCreatedByError is not None


def test_discussion_package_exports_comment_model():
    assert modules.discussion.DiscussionComment is not None
    assert modules.discussion.EmptyCommentIdError is not None
    assert modules.discussion.EmptyCommentThreadIdError is not None
    assert modules.discussion.EmptyCommentBodyError is not None
    assert modules.discussion.EmptyCommentCreatedByError is not None


def test_discussion_package_exports_thread_state_enum():
    assert modules.discussion.ThreadState is not None


def test_discussion_package_exports_repository_interface():
    assert modules.discussion.DiscussionRepository is not None


def test_discussion_package_exports_in_memory_repository():
    assert modules.discussion.InMemoryDiscussionRepository is not None
    assert modules.discussion.DiscussionThreadNotFoundError is not None


def test_discussion_package_exports_service():
    assert modules.discussion.DiscussionService is not None
