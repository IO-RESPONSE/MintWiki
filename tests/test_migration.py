"""Test migration configuration."""

import sys
from pathlib import Path
import asyncio
import tempfile
import importlib
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config as AlembicConfig


def test_migration_env_can_import_settings():
    """Verify migration env.py can import app settings."""
    # Add migrations to path so we can import env
    migrations_path = Path(__file__).parent.parent / "migrations"
    sys.path.insert(0, str(migrations_path))

    try:
        # This should not raise an ImportError
        import env  # noqa: F401
    except ImportError as e:
        raise AssertionError(f"migration env.py failed to import: {e}") from e
    finally:
        # Clean up sys.path
        if str(migrations_path) in sys.path:
            sys.path.remove(str(migrations_path))


def test_migration_directory_exists():
    """Verify migrations directory structure exists."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    assert migrations_dir.exists(), "migrations directory should exist"
    assert (migrations_dir / "env.py").exists(), "migrations/env.py should exist"
    assert (
        migrations_dir / "script.py.mako"
    ).exists(), "migrations/script.py.mako should exist"
    assert (
        migrations_dir / "versions"
    ).exists(), "migrations/versions directory should exist"
    assert (migrations_dir / "versions").is_dir(), "versions should be a directory"


def test_alembic_config_exists():
    """Verify alembic.ini config file exists."""
    alembic_ini = Path(__file__).parent.parent / "alembic.ini"
    assert alembic_ini.exists(), "alembic.ini should exist"


def test_migration_env_uses_shared_metadata():
    """Verify migration env.py uses shared persistence metadata."""
    src_path = Path(__file__).parent.parent / "src"
    migrations_path = Path(__file__).parent.parent / "migrations"

    # Add src and migrations to path
    sys.path.insert(0, str(src_path))
    sys.path.insert(0, str(migrations_path))

    try:
        from persistence.base import metadata
        # Try to import env which should use the metadata
        import env  # noqa: F401

        # Verify that metadata is available
        assert metadata is not None
    except ImportError as e:
        raise AssertionError(
            f"migration env.py failed to import persistence.base: {e}"
        ) from e
    finally:
        # Clean up sys.path
        if str(src_path) in sys.path:
            sys.path.remove(str(src_path))
        if str(migrations_path) in sys.path:
            sys.path.remove(str(migrations_path))


def test_migration_files_are_valid_python():
    """마이그레이션 파일들이 유효한 파이썬 파일인지 확인한다."""
    migrations_versions = (
        Path(__file__).parent.parent / "migrations" / "versions"
    )

    migration_files = sorted(migrations_versions.glob("*.py"))
    migration_files = [f for f in migration_files if not f.name.startswith("_")]

    assert len(migration_files) > 0, "No migration files found"

    for migration_file in migration_files:
        try:
            with open(migration_file, "r") as f:
                compile(f.read(), str(migration_file), "exec")
        except SyntaxError as e:
            raise AssertionError(
                f"Migration file {migration_file.name} has syntax error: {e}"
            ) from e


async def test_migration_smoke_check():
    """마이그레이션 연기 테스트: SQLite 파일 DB에 모든 마이그레이션을 실행한다."""
    import os

    root_dir = Path(__file__).parent.parent

    # 임시 SQLite 파일 생성
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name

    try:
        # SQLite 파일 기반 DB URL
        sync_database_url = f"sqlite:///{db_path}"
        async_database_url = f"sqlite+aiosqlite:///{db_path}"

        # 환경 변수 설정 (Settings가 사용함)
        old_db_url = os.environ.get("WIKI_DATABASE_URL")
        os.environ["WIKI_DATABASE_URL"] = sync_database_url

        try:
            # Alembic 설정 생성
            alembic_cfg = AlembicConfig(str(root_dir / "alembic.ini"))
            alembic_cfg.set_main_option("sqlalchemy.url", sync_database_url)
            alembic_cfg.set_main_option("script_location", str(root_dir / "migrations"))

            try:
                # head 까지 업그레이드
                command.upgrade(alembic_cfg, "head")
            except Exception as e:
                raise AssertionError(f"Migration upgrade failed: {e}") from e
        finally:
            # 환경 변수 복원
            if old_db_url is not None:
                os.environ["WIKI_DATABASE_URL"] = old_db_url
            elif "WIKI_DATABASE_URL" in os.environ:
                del os.environ["WIKI_DATABASE_URL"]

        # 비동기 엔진으로 스키마 검증
        async_engine = create_async_engine(async_database_url, echo=False)
        async with async_engine.begin() as conn:
            # 테이블 조회
            tables = await conn.run_sync(
                lambda c: inspect(c).get_table_names()
            )

            # document 테이블 확인
            assert "document" in tables, "document table should exist"

            # revision 테이블 확인
            assert "revision" in tables, "revision table should exist"

            # document 테이블 열 확인
            doc_columns_result = await conn.run_sync(
                lambda c: inspect(c).get_columns("document")
            )
            doc_col_names = {col["name"] for col in doc_columns_result}

            expected_doc_cols = {
                "id",
                "title",
                "normalized_title",
                "current_revision_id",
                "created_at",
                "updated_at",
            }
            assert expected_doc_cols.issubset(doc_col_names), (
                f"document table is missing columns: "
                f"{expected_doc_cols - doc_col_names}"
            )

            # revision 테이블 열 확인
            rev_columns_result = await conn.run_sync(
                lambda c: inspect(c).get_columns("revision")
            )
            rev_col_names = {col["name"] for col in rev_columns_result}

            expected_rev_cols = {
                "id",
                "document_id",
                "source",
                "author_id",
                "summary",
                "parent_revision_id",
                "created_at",
            }
            assert expected_rev_cols.issubset(rev_col_names), (
                f"revision table is missing columns: "
                f"{expected_rev_cols - rev_col_names}"
            )

        await async_engine.dispose()
    finally:
        # 임시 파일 정리
        import os
        if Path(db_path).exists():
            try:
                os.unlink(db_path)
            except Exception:
                pass


def test_migration_chain_is_continuous():
    """마이그레이션 체인이 연속적인지 확인한다."""
    migrations_versions = (
        Path(__file__).parent.parent / "migrations" / "versions"
    )

    migration_files = sorted(migrations_versions.glob("*.py"))
    migration_files = [
        f for f in migration_files if not f.name.startswith("_")
    ]

    assert len(migration_files) > 0, "No migration files found"

    # 각 마이그레이션의 revision과 down_revision 추출
    revisions = {}

    for migration_file in migration_files:
        with open(migration_file, "r") as f:
            content = f.read()
            # revision 문자열 추출
            revision = None
            down_revision = None

            for line in content.split("\n"):
                if line.strip().startswith("revision = "):
                    revision = line.split("=")[1].strip().strip('"\'')
                if line.strip().startswith("down_revision = "):
                    down_revision_part = line.split("=")[1].strip().strip('"\'')
                    down_revision = (
                        None if down_revision_part == "None" else down_revision_part
                    )

            if revision:
                revisions[revision] = down_revision

    # 체인 검증: 각 revision의 down_revision이 존재하거나 None이어야 함
    for revision, down_revision in revisions.items():
        if down_revision is not None:
            assert down_revision in revisions, (
                f"Migration {revision} references non-existent "
                f"down_revision {down_revision}"
            )

    # 시작점 검증: down_revision이 None인 것이 정확히 하나여야 함
    start_migrations = [
        rev for rev, down_rev in revisions.items() if down_rev is None
    ]
    assert (
        len(start_migrations) == 1
    ), f"Should have exactly 1 root migration, found {len(start_migrations)}: {start_migrations}"
