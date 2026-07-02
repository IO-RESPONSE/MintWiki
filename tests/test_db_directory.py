"""Portable migration 디렉터리 골격(db/)을 검증한다.

docs/migration-portability-checklist.md §6이 확정을 보류했던 PHP 쪽 적용
이력 테이블 이름/실행 방식을 db/README.md가 확정했는지 확인한다.
"""

from pathlib import Path


def _db_dir() -> Path:
    return Path(__file__).parent.parent / "db"


def test_db_directory_exists():
    """db/ 디렉터리와 README가 존재하는지 확인한다."""
    db_dir = _db_dir()
    assert db_dir.exists(), "db directory should exist"
    assert db_dir.is_dir(), "db should be a directory"
    assert (db_dir / "README.md").exists(), "db/README.md should exist"


def test_db_migrations_directory_exists():
    """향후 portable 마이그레이션 원본이 들어갈 db/migrations/가 존재하는지 확인한다."""
    migrations_dir = _db_dir() / "migrations"
    assert migrations_dir.exists(), "db/migrations directory should exist"
    assert migrations_dir.is_dir(), "db/migrations should be a directory"


def test_db_schema_directory_not_yet_created():
    """db/schema는 0460 이후 태스크의 범위이므로 아직 만들지 않는다."""
    schema_dir = _db_dir() / "schema"
    assert not schema_dir.exists(), (
        "db/schema is out of scope for this task (0460+)"
    )


def test_db_readme_confirms_migration_history_table():
    """README가 checklist §6이 보류한 적용 이력 테이블 이름/방식을 확정하는지 확인한다."""
    content = (_db_dir() / "README.md").read_text()

    assert "schema_migration" in content, (
        "README should name the portable migration history table"
    )
    assert "pk_schema_migration" in content, (
        "README should name the primary key constraint"
    )
    assert "version" in content
    assert "created_at" in content
