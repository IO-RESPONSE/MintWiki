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


def test_db_schema_account_sql_exists():
    """0463이 추가한 account.sql이 존재하는지 확인한다."""
    account_sql = _db_dir() / "schema" / "account.sql"
    assert account_sql.exists(), "db/schema/account.sql should exist"


def test_db_schema_account_sql_matches_model_spec():
    """account.sql이 User(model.py)와 같은 컬럼·제약을 갖는지 확인한다."""
    content = (_db_dir() / "schema" / "account.sql").read_text()

    assert "CREATE TABLE account" in content
    assert "id VARCHAR(255) NOT NULL" in content
    assert "username VARCHAR(255) NOT NULL" in content
    assert "display_name VARCHAR(255) NULL" in content
    assert "CONSTRAINT pk_account PRIMARY KEY (id)" in content
    assert "CONSTRAINT uq_account_username UNIQUE (username)" in content


def test_db_schema_account_sql_separates_dialect_differences_in_comments():
    """PostgreSQL/MariaDB 차이가 주석으로 분리되어 있는지 확인한다(0461과 동일 패턴)."""
    content = (_db_dir() / "schema" / "account.sql").read_text()

    assert "PostgreSQL" in content
    assert "MariaDB" in content
    # 실제 CREATE TABLE 문에는 방언 전용 문법이 섞이지 않는다.
    create_table_stmt = content[content.index("CREATE TABLE") :]
    assert "WITH TIME ZONE" not in create_table_stmt
    assert "COLLATE" not in create_table_stmt
    assert "AUTO_INCREMENT" not in create_table_stmt
    assert "SERIAL" not in create_table_stmt


def test_db_schema_user_session_sql_exists():
    """0464가 추가한 user_session.sql이 존재하는지 확인한다."""
    user_session_sql = _db_dir() / "schema" / "user_session.sql"
    assert user_session_sql.exists(), "db/schema/user_session.sql should exist"


def test_db_schema_user_session_sql_matches_plan_spec():
    """user_session.sql이 Session/SessionRepository와 계획 문서 §3과 같은 컬럼·제약을 갖는지 확인한다."""
    content = (_db_dir() / "schema" / "user_session.sql").read_text()

    assert "CREATE TABLE user_session" in content
    assert "id VARCHAR(255) NOT NULL" in content
    assert "account_id VARCHAR(255) NOT NULL" in content
    assert "created_at TIMESTAMP NOT NULL" in content
    assert "expires_at TIMESTAMP NOT NULL" in content
    assert "CONSTRAINT pk_user_session PRIMARY KEY (id)" in content
    assert (
        "CONSTRAINT fk_user_session_account_id FOREIGN KEY (account_id) "
        "REFERENCES account (id)" in content
    )


def test_db_schema_user_session_sql_separates_dialect_differences_in_comments():
    """PostgreSQL/MariaDB 차이가 주석으로 분리되어 있는지 확인한다(0461과 동일 패턴)."""
    content = (_db_dir() / "schema" / "user_session.sql").read_text()

    assert "PostgreSQL" in content
    assert "MariaDB" in content
    # 실제 CREATE TABLE 문에는 방언 전용 문법이 섞이지 않는다.
    create_table_stmt = content[content.index("CREATE TABLE") :]
    assert "WITH TIME ZONE" not in create_table_stmt
    assert "COLLATE" not in create_table_stmt
    assert "AUTO_INCREMENT" not in create_table_stmt
    assert "SERIAL" not in create_table_stmt


def test_db_schema_acl_rule_sql_exists():
    """0465가 추가한 acl_rule.sql이 존재하는지 확인한다."""
    acl_rule_sql = _db_dir() / "schema" / "acl_rule.sql"
    assert acl_rule_sql.exists(), "db/schema/acl_rule.sql should exist"


def test_db_schema_acl_rule_sql_matches_plan_spec():
    """acl_rule.sql이 Rule/DocumentAcl과 계획 문서 §3과 같은 컬럼·제약을 갖는지 확인한다."""
    content = (_db_dir() / "schema" / "acl_rule.sql").read_text()

    assert "CREATE TABLE acl_rule" in content
    assert "id VARCHAR(255) NOT NULL" in content
    assert "document_id VARCHAR(255) NOT NULL" in content
    assert "subject_type VARCHAR(20) NOT NULL" in content
    assert "subject_id VARCHAR(255) NULL" in content
    assert "permission VARCHAR(20) NOT NULL" in content
    assert "effect VARCHAR(10) NOT NULL" in content
    assert "expires_at TIMESTAMP NULL" in content
    assert "sort_order INTEGER NOT NULL" in content
    assert "CONSTRAINT pk_acl_rule PRIMARY KEY (id)" in content
    assert (
        "CONSTRAINT fk_acl_rule_document_id FOREIGN KEY (document_id) "
        "REFERENCES document (id)" in content
    )
    assert (
        "CONSTRAINT uq_acl_rule_document_id_sort_order UNIQUE "
        "(document_id, sort_order)" in content
    )


def test_db_schema_acl_rule_sql_separates_dialect_differences_in_comments():
    """PostgreSQL/MariaDB 차이가 주석으로 분리되어 있는지 확인한다(0461과 동일 패턴)."""
    content = (_db_dir() / "schema" / "acl_rule.sql").read_text()

    assert "PostgreSQL" in content
    assert "MariaDB" in content
    # 실제 CREATE TABLE 문에는 방언 전용 문법이 섞이지 않는다.
    create_table_stmt = content[content.index("CREATE TABLE") :]
    assert "WITH TIME ZONE" not in create_table_stmt
    assert "COLLATE" not in create_table_stmt
    assert "AUTO_INCREMENT" not in create_table_stmt
    assert "SERIAL" not in create_table_stmt


def test_db_schema_acl_namespace_rule_sql_exists():
    """0465가 추가한 acl_namespace_rule.sql이 존재하는지 확인한다."""
    acl_namespace_rule_sql = _db_dir() / "schema" / "acl_namespace_rule.sql"
    assert acl_namespace_rule_sql.exists(), (
        "db/schema/acl_namespace_rule.sql should exist"
    )


def test_db_schema_acl_namespace_rule_sql_matches_plan_spec():
    """acl_namespace_rule.sql이 NamespaceAclDefaults와 계획 문서 §4와 같은 컬럼·제약을 갖는지 확인한다."""
    content = (_db_dir() / "schema" / "acl_namespace_rule.sql").read_text()

    assert "CREATE TABLE acl_namespace_rule" in content
    assert "id VARCHAR(255) NOT NULL" in content
    assert "namespace VARCHAR(255) NOT NULL" in content
    assert "subject_type VARCHAR(20) NOT NULL" in content
    assert "subject_id VARCHAR(255) NULL" in content
    assert "permission VARCHAR(20) NOT NULL" in content
    assert "effect VARCHAR(10) NOT NULL" in content
    assert "expires_at TIMESTAMP NULL" in content
    assert "sort_order INTEGER NOT NULL" in content
    assert "CONSTRAINT pk_acl_namespace_rule PRIMARY KEY (id)" in content
    assert (
        "CONSTRAINT uq_acl_namespace_rule_namespace_sort_order UNIQUE "
        "(namespace, sort_order)" in content
    )
    # namespace는 FK 대상 테이블이 없는 자유 문자열이라 FK 제약이 없다.
    assert "FOREIGN KEY" not in content


def test_db_schema_acl_namespace_rule_sql_separates_dialect_differences_in_comments():
    """PostgreSQL/MariaDB 차이가 주석으로 분리되어 있는지 확인한다(0461과 동일 패턴)."""
    content = (_db_dir() / "schema" / "acl_namespace_rule.sql").read_text()

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
