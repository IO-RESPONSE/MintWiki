"""PostgreSQL DSN 호환 문서(0471)를 검증한다.

docs/postgresql-dsn-compatibility.md가 기존 개발 환경(config.py,
.env.example)의 PostgreSQL DSN과 0470이 추가한 MariaDB DSN placeholder를
실제로 연결해 문서화했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "postgresql-dsn-compatibility.md"


def test_postgresql_dsn_compatibility_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/postgresql-dsn-compatibility.md should exist"


def test_postgresql_dsn_compatibility_doc_references_current_env_values():
    """문서가 실제 .env.example/config.py 기본값을 그대로 인용하는지 확인한다."""
    content = _doc_path().read_text()

    assert "WIKI_DATABASE_URL=postgresql://wiki:wiki@localhost:5432/wiki_engine" in content
    assert "WIKI_MARIADB_DSN=mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine" in content
    assert "postgresql+asyncpg" in content


def test_postgresql_dsn_compatibility_doc_links_to_related_policy_docs():
    """이 문서가 기존 DB 정책 문서와 설정 소스를 연결하는지 확인한다."""
    content = _doc_path().read_text()

    assert "mariadb-compatibility-matrix.md" in content
    assert "ansi-sql-persistence-policy.md" in content
    assert "../src/app/config.py" in content
    assert "../.env.example" in content


def test_postgresql_dsn_compatibility_doc_does_not_change_driver_behavior():
    """드라이버 전환은 이 태스크 범위 밖임을 문서가 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "드라이버 전환을 다루지 않는다" in content
