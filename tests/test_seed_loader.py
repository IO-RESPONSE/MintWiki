"""
Portable seed fixture 로더 테스트.
"""

import pytest
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from persistence.base import Base
from persistence.models import DocumentORM, RevisionORM
from persistence.seed_loader import SeedLoader


@pytest.fixture
async def test_db():
    """테스트용 임시 데이터베이스를 생성한다."""
    # 비동기 SQLite 인메모리 데이터베이스
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # 모든 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    yield engine, async_session

    await engine.dispose()


class TestSeedLoaderBasics:
    """SeedLoader 기본 기능 테스트."""

    def test_seed_loader_initialization(self):
        """SeedLoader를 초기화할 수 있는지 확인한다."""
        loader = SeedLoader()
        assert loader is not None
        assert loader.fixtures_dir.exists()
        assert loader.fixtures_dir.name == "seed"

    def test_seed_loader_with_custom_path(self):
        """커스텀 경로로 SeedLoader를 초기화할 수 있는지 확인한다."""
        custom_path = Path(__file__).parent / "fixtures" / "seed"
        loader = SeedLoader(fixtures_dir=custom_path)
        assert loader.fixtures_dir == custom_path

    def test_seed_files_exist(self):
        """기본 seed 파일들이 존재하는지 확인한다."""
        loader = SeedLoader()
        documents_file = loader.fixtures_dir / "documents.sql"
        revisions_file = loader.fixtures_dir / "revisions.sql"

        assert documents_file.exists()
        assert revisions_file.exists()


class TestSeedLoaderParsing:
    """SeedLoader의 SQL 파싱 기능 테스트."""

    def test_parse_simple_insert(self):
        """단순 INSERT 문을 파싱할 수 있는지 확인한다."""
        loader = SeedLoader()
        sql = """
        INSERT INTO test_table (id, name)
        VALUES ('1', 'Test');
        """

        statements = loader._parse_insert_statements(sql)

        assert len(statements) == 1
        assert "INSERT INTO" in statements[0]
        assert "test_table" in statements[0]

    def test_parse_multiple_inserts(self):
        """여러 INSERT 문을 파싱할 수 있는지 확인한다."""
        loader = SeedLoader()
        sql = """
        INSERT INTO table1 (id) VALUES ('1');
        INSERT INTO table2 (id) VALUES ('2');
        """

        statements = loader._parse_insert_statements(sql)

        assert len(statements) == 2

    def test_parse_removes_line_comments(self):
        """라인 주석(--로 시작)을 제거할 수 있는지 확인한다."""
        loader = SeedLoader()
        sql = """
        -- 이것은 주석입니다
        INSERT INTO test_table (id) VALUES ('1'); -- 인라인 주석
        """

        statements = loader._parse_insert_statements(sql)

        assert len(statements) == 1
        # 주석이 제거되어야 함
        assert "--" not in statements[0]

    def test_parse_removes_block_comments(self):
        """블록 주석(/* ... */)을 제거할 수 있는지 확인한다."""
        loader = SeedLoader()
        sql = """
        /* 이것은 블록 주석입니다 */
        INSERT INTO test_table (id) VALUES ('1');
        """

        statements = loader._parse_insert_statements(sql)

        assert len(statements) == 1

    def test_parse_multiline_values(self):
        """여러 줄에 걸친 VALUES를 파싱할 수 있는지 확인한다."""
        loader = SeedLoader()
        sql = """
        INSERT INTO test_table (id, name)
        VALUES (
            'id-1',
            'Test Name'
        );
        """

        statements = loader._parse_insert_statements(sql)

        assert len(statements) == 1


class TestSeedLoaderLoading:
    """SeedLoader의 데이터 로딩 기능 테스트."""

    @pytest.mark.asyncio
    async def test_load_documents_seed(self, test_db):
        """문서 seed를 로드할 수 있는지 확인한다."""
        engine, async_session = test_db
        loader = SeedLoader()

        async with async_session() as session:
            await loader.load_seed(session, "documents")

            # 로드된 데이터 확인
            result = await session.execute(select(DocumentORM))
            documents = result.scalars().all()

            # 3개의 문서가 로드되어야 함
            assert len(documents) == 3
            assert documents[0].title == "Home"
            assert documents[1].title == "Documentation"
            assert documents[2].title == "Test Page"

    @pytest.mark.asyncio
    async def test_load_revisions_seed(self, test_db):
        """리비전 seed를 로드할 수 있는지 확인한다."""
        engine, async_session = test_db
        loader = SeedLoader()

        async with async_session() as session:
            # 먼저 문서를 로드 (FK 종속성)
            await loader.load_seed(session, "documents")
            # 리비전 로드
            await loader.load_seed(session, "revisions")

            # 로드된 데이터 확인
            result = await session.execute(select(RevisionORM))
            revisions = result.scalars().all()

            # 4개의 리비전이 로드되어야 함
            assert len(revisions) == 4

    @pytest.mark.asyncio
    async def test_load_all_seeds(self, test_db):
        """모든 seed를 로드할 수 있는지 확인한다."""
        engine, async_session = test_db
        loader = SeedLoader()

        async with async_session() as session:
            await loader.load_all_seeds(session)

            # 문서 개수 확인
            doc_result = await session.execute(select(DocumentORM))
            documents = doc_result.scalars().all()
            assert len(documents) == 3

            # 리비전 개수 확인
            rev_result = await session.execute(select(RevisionORM))
            revisions = rev_result.scalars().all()
            assert len(revisions) == 4

    @pytest.mark.asyncio
    async def test_load_nonexistent_seed_raises_error(self, test_db):
        """존재하지 않는 seed 파일을 로드하려 하면 에러가 발생한다."""
        engine, async_session = test_db
        loader = SeedLoader()

        async with async_session() as session:
            with pytest.raises(FileNotFoundError):
                await loader.load_seed(session, "nonexistent_table")


class TestSeedDataIntegrity:
    """Seed 데이터 무결성 테스트."""

    @pytest.mark.asyncio
    async def test_documents_have_correct_values(self, test_db):
        """로드된 문서의 값이 정확한지 확인한다."""
        engine, async_session = test_db
        loader = SeedLoader()

        async with async_session() as session:
            await loader.load_seed(session, "documents")

            result = await session.execute(
                select(DocumentORM).where(
                    DocumentORM.title == "Home"
                )
            )
            doc = result.scalar_one()

            assert doc.id == "doc-00001-0000-0000-0000-000000000000"
            assert doc.title == "Home"
            assert doc.normalized_title == "Home"
            assert doc.current_revision_id == "rev-00001-0000-0000-0000-000000000000"

    @pytest.mark.asyncio
    async def test_revisions_have_correct_fk_references(self, test_db):
        """로드된 리비전의 FK 참조가 정확한지 확인한다."""
        engine, async_session = test_db
        loader = SeedLoader()

        async with async_session() as session:
            await loader.load_all_seeds(session)

            # 첫 번째 리비전 확인 (parent_revision_id가 NULL)
            result = await session.execute(
                select(RevisionORM).where(
                    RevisionORM.id == "rev-00001-0000-0000-0000-000000000000"
                )
            )
            rev = result.scalar_one()

            assert rev.document_id == "doc-00001-0000-0000-0000-000000000000"
            assert rev.parent_revision_id is None
            assert rev.author_id == "user-00001-0000-0000-0000-000000000000"

    @pytest.mark.asyncio
    async def test_revisions_with_parent_references(self, test_db):
        """부모 리비전을 참조하는 리비전을 확인한다."""
        engine, async_session = test_db
        loader = SeedLoader()

        async with async_session() as session:
            await loader.load_all_seeds(session)

            # 세 번째 리비전 (부모가 있음)
            result = await session.execute(
                select(RevisionORM).where(
                    RevisionORM.id == "rev-00003-0000-0000-0000-000000000000"
                )
            )
            rev = result.scalar_one()

            assert rev.parent_revision_id == "rev-00001-0000-0000-0000-000000000000"
