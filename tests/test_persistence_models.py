"""ORM 모델 테스트."""

from persistence.models import DocumentORM
from modules.document.model import Document


class TestDocumentORM:
    """DocumentORM 테스트."""

    def test_document_orm_has_tablename(self):
        """DocumentORM이 올바른 테이블 이름을 가지고 있는지 확인한다."""
        assert DocumentORM.__tablename__ == "document"

    def test_document_orm_has_required_columns(self):
        """DocumentORM이 필수 컬럼을 가지고 있는지 확인한다."""
        assert hasattr(DocumentORM, "id")
        assert hasattr(DocumentORM, "title")
        assert hasattr(DocumentORM, "normalized_title")
        assert hasattr(DocumentORM, "current_revision_id")
        assert hasattr(DocumentORM, "created_at")
        assert hasattr(DocumentORM, "updated_at")

    def test_document_orm_from_domain(self):
        """도메인 모델에서 ORM 모델을 생성한다."""
        domain_doc = Document(
            id="doc1",
            title="Test Document",
            current_revision_id="rev1",
        )

        orm_doc = DocumentORM.from_domain(domain_doc)

        assert orm_doc.id == "doc1"
        assert orm_doc.title == "Test Document"
        assert orm_doc.normalized_title == "Test Document"
        assert orm_doc.current_revision_id == "rev1"

    def test_document_orm_to_domain(self):
        """ORM 모델을 도메인 모델로 변환한다."""
        orm_doc = DocumentORM(
            id="doc1",
            title="Test Document",
            normalized_title="Test Document",
            current_revision_id="rev1",
        )

        domain_doc = orm_doc.to_domain()

        assert isinstance(domain_doc, Document)
        assert domain_doc.id == "doc1"
        assert domain_doc.title == "Test Document"
        assert domain_doc.normalized_title == "Test Document"
        assert domain_doc.current_revision_id == "rev1"

    def test_document_orm_round_trip(self):
        """도메인 모델 -> ORM 모델 -> 도메인 모델 변환이 정보를 보존한다."""
        original = Document(
            id="doc2",
            title="Another Document",
            current_revision_id=None,
        )

        orm = DocumentORM.from_domain(original)
        restored = orm.to_domain()

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.normalized_title == original.normalized_title
        assert restored.current_revision_id == original.current_revision_id

    def test_document_orm_without_current_revision(self):
        """현재 리비전 없이 ORM 모델을 생성한다."""
        orm_doc = DocumentORM(
            id="doc3",
            title="No Revision Document",
            normalized_title="No Revision Document",
            current_revision_id=None,
        )

        assert orm_doc.id == "doc3"
        assert orm_doc.title == "No Revision Document"
        assert orm_doc.current_revision_id is None

    def test_document_orm_metadata_registered(self):
        """DocumentORM이 공유 메타데이터에 등록되는지 확인한다."""
        from persistence.base import metadata

        assert "document" in metadata.tables
        table = metadata.tables["document"]
        assert "id" in table.columns
        assert "title" in table.columns
        assert "normalized_title" in table.columns
