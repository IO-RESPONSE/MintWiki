"""리비전 모델 테스트."""
from modules.revision.model import Revision


class TestRevisionConstruction:
    """리비전 생성 테스트."""

    def test_creates_revision_with_required_fields(self):
        """필수 필드로 리비전을 생성한다."""
        revision = Revision(
            id="rev1",
            document_id="doc1",
            source="Hello, World!",
            author_id="user1",
            summary="Initial content",
        )
        assert revision.id == "rev1"
        assert revision.document_id == "doc1"
        assert revision.source == "Hello, World!"
        assert revision.author_id == "user1"
        assert revision.summary == "Initial content"
        assert revision.parent_revision_id is None

    def test_creates_first_revision_without_parent(self):
        """첫 리비전을 부모 없이 생성한다."""
        revision = Revision(
            id="rev1",
            document_id="doc1",
            source="Initial content",
            author_id="user1",
            summary="Create document",
        )
        assert revision.id == "rev1"
        assert revision.parent_revision_id is None

    def test_creates_revision_with_parent(self):
        """부모 리비전을 포함하여 리비전을 생성한다."""
        revision = Revision(
            id="rev2",
            document_id="doc1",
            source="Updated content",
            author_id="user2",
            summary="Update content",
            parent_revision_id="rev1",
        )
        assert revision.id == "rev2"
        assert revision.document_id == "doc1"
        assert revision.source == "Updated content"
        assert revision.author_id == "user2"
        assert revision.summary == "Update content"
        assert revision.parent_revision_id == "rev1"

    def test_stores_all_fields(self):
        """모든 필드를 올바르게 저장한다."""
        revision = Revision(
            id="rev3",
            document_id="doc2",
            source="Multi-line\ncontent\nhere",
            author_id="user3",
            summary="Complex edit",
            parent_revision_id="rev2",
        )
        assert revision.id == "rev3"
        assert revision.document_id == "doc2"
        assert revision.source == "Multi-line\ncontent\nhere"
        assert revision.author_id == "user3"
        assert revision.summary == "Complex edit"
        assert revision.parent_revision_id == "rev2"
