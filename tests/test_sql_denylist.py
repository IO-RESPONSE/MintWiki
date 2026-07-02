"""scripts/check_sql_denylist.py 에 대한 테스트."""
import sys
from pathlib import Path

import pytest

# scripts/ 는 pythonpath 에 포함되지 않으므로 임시로 추가한다.
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_sql_denylist  # noqa: E402


REPO_ROOT = Path(__file__).parent.parent


@pytest.mark.parametrize(
    "snippet",
    [
        "result = await session.execute(query.returning(Document.id))",
        "stmt = text('UPDATE document SET title = :title RETURNING id')",
        "documents = query.filter(Document.title.ilike(f'%{term}%'))",
        "column('metadata', JSONB)",
        "value = row['data->>title']",
        "tags = Column(postgresql.ARRAY(String))",
        "id = Column(Integer, Sequence('id_seq'), primary_key=True)  # SERIAL",
        "default=text('gen_random_uuid()')",
        "default=text('uuid_generate_v4()')",
        "stmt = insert(Document).on_conflict_do_update(index_elements=['id'])",
        "stmt = select(Job).with_for_update(skip_locked=True)",
        "column('search_vector', TSVECTOR)",
        "query = query.distinct(Document.author_id)  # DISTINCT ON",
        "text('SELECT generate_series(1, 10)')",
        "text('LISTEN document_changes')",
        "text('CREATE TABLE child () INHERITS (parent)')",
        "op.create_index('ix_active', 'document', ['id'], postgresql_where=text('active'))",
        "text(\"CREATE TYPE mood AS ENUM ('happy', 'sad')\")",
        "text('SELECT age(created_at)')",
        "text('SELECT date_trunc(\\'day\\', created_at)')",
    ],
)
def test_check_file_detects_denylisted_features(tmp_path, snippet):
    """정책 문서의 금지 목록 항목이 코드에 등장하면 위반으로 탐지되어야 한다."""
    target = tmp_path / "repository.py"
    target.write_text(snippet, encoding="utf-8")

    violations = check_sql_denylist.check_file(target)

    assert violations, f"'{snippet}' 는 위반으로 탐지되어야 한다"


def test_check_file_allows_portable_sql(tmp_path):
    """ANSI SQL/portable 표현은 위반으로 탐지되지 않아야 한다."""
    target = tmp_path / "repository.py"
    target.write_text(
        "\n".join(
            [
                "async def get_by_id(self, document_id: str) -> Document | None:",
                "    stmt = select(Document).where(Document.id == document_id)",
                "    result = await self.session.execute(stmt)",
                "    return result.scalar_one_or_none()",
                "",
                "def resolve(self) -> str:",
                "    return self._value",
            ]
        ),
        encoding="utf-8",
    )

    assert check_sql_denylist.check_file(target) == []


def test_iter_target_files_covers_repository_persistence_and_migrations(tmp_path):
    """검사 대상 glob 이 정책 문서의 적용 범위(저장소/영속성/마이그레이션)를 포함해야 한다."""
    (tmp_path / "src" / "modules" / "document").mkdir(parents=True)
    (tmp_path / "src" / "modules" / "document" / "repository.py").write_text(
        "", encoding="utf-8"
    )
    (tmp_path / "src" / "persistence").mkdir(parents=True)
    (tmp_path / "src" / "persistence" / "models.py").write_text("", encoding="utf-8")
    (tmp_path / "migrations" / "versions").mkdir(parents=True)
    (tmp_path / "migrations" / "versions" / "0001_initial.py").write_text(
        "", encoding="utf-8"
    )
    (tmp_path / "db" / "schema").mkdir(parents=True)
    (tmp_path / "db" / "schema" / "document.sql").write_text("", encoding="utf-8")

    files = check_sql_denylist.iter_target_files(tmp_path)

    relative = {str(path.relative_to(tmp_path)) for path in files}
    assert "src/modules/document/repository.py" in relative
    assert "src/persistence/models.py" in relative
    assert "migrations/versions/0001_initial.py" in relative
    assert "db/schema/document.sql" in relative


@pytest.mark.parametrize(
    "snippet",
    [
        "UPDATE document SET title = :title RETURNING id;",
        "SELECT * FROM document WHERE title ILIKE '%term%';",
        "CREATE TABLE t (metadata JSONB NOT NULL);",
        "CREATE TABLE t (tags ARRAY NOT NULL);",
        "id BIGSERIAL PRIMARY KEY",
        "id VARCHAR(255) NOT NULL DEFAULT gen_random_uuid()",
        "INSERT INTO t (id) VALUES (1) ON CONFLICT (id) DO UPDATE SET id = 1;",
        "SELECT * FROM job FOR UPDATE SKIP LOCKED;",
        "CREATE TABLE t (body TSVECTOR);",
        "SELECT DISTINCT ON (author_id) * FROM document;",
        "SELECT generate_series(1, 10);",
        "LISTEN document_changes;",
        "CREATE TABLE child () INHERITS (parent);",
        "CREATE INDEX ix_active ON document (id) WHERE active;",
        "CREATE TYPE mood AS ENUM ('happy', 'sad');",
        "SELECT age(created_at);",
    ],
)
def test_check_file_detects_denylisted_features_in_sql_files(tmp_path, snippet):
    """db/schema/*.sql 처럼 .sql 확장자를 가진 파일에서도 금지 목록이 탐지되어야 한다."""
    target = tmp_path / "table.sql"
    target.write_text(snippet, encoding="utf-8")

    violations = check_sql_denylist.check_file(target)

    assert violations, f"'{snippet}' 는 .sql 파일에서도 위반으로 탐지되어야 한다"


def test_check_file_ignores_sql_comments_mentioning_denylisted_features(tmp_path):
    """db/schema/*.sql 의 PostgreSQL/MariaDB 차이 설명 주석은 위반으로 탐지되면 안 된다.

    document.sql 등은 "PostgreSQL SERIAL/gen_random_uuid()..." 처럼 금지 기능
    이름을 설명 목적으로 주석에 인용한다 — 이는 실제 DDL이 아니므로 오탐이면
    안 된다.
    """
    target = tmp_path / "document.sql"
    target.write_text(
        "\n".join(
            [
                "-- id: PostgreSQL SERIAL/gen_random_uuid(), MariaDB",
                "-- AUTO_INCREMENT/UUID() 어느 쪽도 쓰지 않는다.",
                "-- ILIKE, JSONB, RETURNING 은 모두 금지 목록에 있다.",
                "CREATE TABLE document (",
                "    id VARCHAR(255) NOT NULL,",
                "    CONSTRAINT pk_document PRIMARY KEY (id)",
                ");",
            ]
        ),
        encoding="utf-8",
    )

    assert check_sql_denylist.check_file(target) == []


def test_check_file_detects_violation_before_sql_comment_on_same_line(tmp_path):
    """같은 줄에서 주석 앞의 실제 SQL 코드에 있는 위반은 여전히 탐지되어야 한다."""
    target = tmp_path / "table.sql"
    target.write_text(
        "id BIGSERIAL PRIMARY KEY, -- 참고용 주석\n", encoding="utf-8"
    )

    violations = check_sql_denylist.check_file(target)

    assert violations
    assert any("SERIAL" in v for v in violations)


def test_main_schema_sql_files_pass_denylist(monkeypatch):
    """db/schema/*.sql 파일들은 현재 금지 목록을 위반하지 않아야 한다 (회귀 방지)."""
    schema_dir = REPO_ROOT / "db" / "schema"
    sql_files = sorted(schema_dir.glob("*.sql"))

    assert sql_files, "db/schema 에 검사할 .sql 파일이 있어야 한다"

    violations = []
    for path in sql_files:
        violations.extend(check_sql_denylist.check_file(path))

    assert violations == []


def test_main_passes_on_current_repository(monkeypatch, capsys):
    """현재 저장소 코드는 금지 목록을 위반하지 않아야 한다 (회귀 방지)."""
    monkeypatch.chdir(REPO_ROOT)

    exit_code = check_sql_denylist.main()

    captured = capsys.readouterr()
    assert exit_code == 0, captured.err
