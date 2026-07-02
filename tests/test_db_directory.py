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


def test_db_schema_directory_exists():
    """0460이 만든 db/schema 디렉터리와 base 테이블 초안을 확인한다."""
    schema_dir = _db_dir() / "schema"
    assert schema_dir.exists(), "db/schema directory should exist"
    assert schema_dir.is_dir(), "db/schema should be a directory"
    assert (schema_dir / "README.md").exists(), "db/schema/README.md should exist"
    assert (schema_dir / "schema_migration.sql").exists(), (
        "db/schema/schema_migration.sql should exist"
    )


def test_db_schema_migration_sql_matches_readme_spec():
    """schema_migration.sql이 db/README.md가 확정한 스펙과 일치하는지 확인한다."""
    content = (_db_dir() / "schema" / "schema_migration.sql").read_text()

    assert "CREATE TABLE schema_migration" in content
    assert "version" in content
    assert "created_at" in content
    assert "CONSTRAINT pk_schema_migration PRIMARY KEY" in content


def test_db_schema_document_sql_exists():
    """0461이 추가한 document.sql이 존재하는지 확인한다."""
    document_sql = _db_dir() / "schema" / "document.sql"
    assert document_sql.exists(), "db/schema/document.sql should exist"


def test_db_schema_document_sql_matches_orm_spec():
    """document.sql이 DocumentORM/0002 마이그레이션과 같은 컬럼·제약을 갖는지 확인한다."""
    content = (_db_dir() / "schema" / "document.sql").read_text()

    assert "CREATE TABLE document" in content
    assert "id VARCHAR(255) NOT NULL" in content
    assert "title VARCHAR(500) NOT NULL" in content
    assert "normalized_title VARCHAR(500) NOT NULL" in content
    assert "current_revision_id VARCHAR(255) NULL" in content
    assert "created_at TIMESTAMP NOT NULL" in content
    assert "updated_at TIMESTAMP NOT NULL" in content
    assert "CONSTRAINT pk_document PRIMARY KEY (id)" in content
    assert "CONSTRAINT uq_document_normalized_title UNIQUE (normalized_title)" in content


def test_db_schema_document_sql_separates_dialect_differences_in_comments():
    """PostgreSQL/MariaDB 차이가 주석으로 분리되어 있는지 확인한다(0461 노트)."""
    content = (_db_dir() / "schema" / "document.sql").read_text()

    assert "PostgreSQL" in content
    assert "MariaDB" in content
    # 실제 CREATE TABLE 문에는 방언 전용 문법이 섞이지 않는다.
    create_table_stmt = content[content.index("CREATE TABLE") :]
    assert "WITH TIME ZONE" not in create_table_stmt
    assert "COLLATE" not in create_table_stmt
    assert "AUTO_INCREMENT" not in create_table_stmt
    assert "SERIAL" not in create_table_stmt


def test_db_schema_revision_sql_exists():
    """0462가 추가한 revision.sql이 존재하는지 확인한다."""
    revision_sql = _db_dir() / "schema" / "revision.sql"
    assert revision_sql.exists(), "db/schema/revision.sql should exist"


def test_db_schema_revision_sql_matches_orm_spec():
    """revision.sql이 RevisionORM/0003 마이그레이션과 같은 컬럼·제약을 갖는지 확인한다."""
    content = (_db_dir() / "schema" / "revision.sql").read_text()

    assert "CREATE TABLE revision" in content
    assert "id VARCHAR(255) NOT NULL" in content
    assert "document_id VARCHAR(255) NOT NULL" in content
    assert "source TEXT NOT NULL" in content
    assert "author_id VARCHAR(255) NOT NULL" in content
    assert "summary VARCHAR(500) NOT NULL" in content
    assert "parent_revision_id VARCHAR(255) NULL" in content
    assert "created_at TIMESTAMP NOT NULL" in content
    assert "CONSTRAINT pk_revision PRIMARY KEY (id)" in content
    assert (
        "CONSTRAINT fk_revision_document_id FOREIGN KEY (document_id) "
        "REFERENCES document (id)" in content
    )


def test_db_schema_revision_sql_separates_dialect_differences_in_comments():
    """PostgreSQL/MariaDB 차이가 주석으로 분리되어 있는지 확인한다(0461과 동일 패턴)."""
    content = (_db_dir() / "schema" / "revision.sql").read_text()

    assert "PostgreSQL" in content
    assert "MariaDB" in content
    # 실제 CREATE TABLE 문에는 방언 전용 문법이 섞이지 않는다.
    create_table_stmt = content[content.index("CREATE TABLE") :]
    assert "WITH TIME ZONE" not in create_table_stmt
    assert "COLLATE" not in create_table_stmt
    assert "AUTO_INCREMENT" not in create_table_stmt
    assert "SERIAL" not in create_table_stmt


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
