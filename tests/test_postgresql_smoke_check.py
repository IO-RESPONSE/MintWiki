"""scripts/postgresql_smoke_check.py 에 대한 테스트.

실제 PostgreSQL 서버가 없는 CI/로컬 환경에서도 항상 통과해야 하므로,
"DB가 없으면(또는 psql이 없으면/접속이 실패하면) skip한다" 규칙과
순서/DSN 파싱 같은 순수 로직만 검증한다. 실제 서버 접속/DDL 적용 경로는
PostgreSQL이 준비된 환경에서 수동으로 확인한다(smoke 스크립트 자체가 그
skip 로직을 갖는 이유).
"""
import sys
from pathlib import Path

import pytest

# scripts/ 는 pythonpath 에 포함되지 않으므로 임시로 추가한다.
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import postgresql_smoke_check  # noqa: E402


REPO_ROOT = Path(__file__).parent.parent


def test_schema_order_matches_mariadb_smoke_check_fk_dependency_order():
    """db/schema는 두 DB가 공유하므로 mariadb_smoke_check.py와 같은 순서여야 한다."""
    import mariadb_smoke_check  # noqa: E402

    assert postgresql_smoke_check.SCHEMA_ORDER == mariadb_smoke_check.SCHEMA_ORDER


def test_schema_order_covers_every_file_in_db_schema():
    """SCHEMA_ORDER가 db/schema/*.sql 파일 전체를 빠짐없이 포함하는지 확인한다."""
    actual_files = {p.name for p in (REPO_ROOT / "db" / "schema").glob("*.sql")}
    assert set(postgresql_smoke_check.SCHEMA_ORDER) == actual_files


def test_parse_dsn_extracts_connection_parts():
    """postgresql:// DSN을 host/port/user/password/database로 분해하는지 확인한다."""
    conn = postgresql_smoke_check.parse_dsn(
        "postgresql://wiki:wiki@localhost:5432/wiki_engine"
    )

    assert conn == {
        "user": "wiki",
        "password": "wiki",
        "host": "localhost",
        "port": 5432,
        "database": "wiki_engine",
    }


def test_parse_dsn_falls_back_to_default_port():
    """포트가 생략된 DSN은 기본 PostgreSQL 포트(5432)를 쓰는지 확인한다."""
    conn = postgresql_smoke_check.parse_dsn("postgresql://wiki:wiki@localhost/wiki_engine")

    assert conn["port"] == 5432


def test_resolve_dsn_returns_none_when_unset(monkeypatch):
    """환경 변수와 .env 파일 어디에도 없으면 None을 반환하는지 확인한다."""
    monkeypatch.delenv(postgresql_smoke_check.DSN_ENV_VAR, raising=False)
    monkeypatch.setattr(postgresql_smoke_check, "ENV_FILE", Path("/nonexistent/.env"))

    assert postgresql_smoke_check.resolve_dsn() is None


def test_resolve_dsn_prefers_environment_variable(monkeypatch):
    """환경 변수가 있으면 .env 파일보다 우선하는지 확인한다."""
    monkeypatch.setenv(postgresql_smoke_check.DSN_ENV_VAR, "postgresql://env/db")

    assert postgresql_smoke_check.resolve_dsn() == "postgresql://env/db"


def test_main_skips_when_dsn_not_configured(monkeypatch, capsys):
    """DSN이 없으면 실패가 아니라 skip(종료 코드 0)으로 끝나는지 확인한다."""
    monkeypatch.delenv(postgresql_smoke_check.DSN_ENV_VAR, raising=False)
    monkeypatch.setattr(postgresql_smoke_check, "ENV_FILE", Path("/nonexistent/.env"))

    exit_code = postgresql_smoke_check.main()

    assert exit_code == 0
    assert "skip" in capsys.readouterr().out


def test_main_skips_when_psql_client_missing(monkeypatch, capsys):
    """psql CLI가 없으면 접속을 시도하지 않고 skip하는지 확인한다."""
    monkeypatch.setenv(postgresql_smoke_check.DSN_ENV_VAR, "postgresql://wiki:wiki@localhost/wiki_engine")
    monkeypatch.setattr(postgresql_smoke_check, "_psql_client", lambda: None)

    exit_code = postgresql_smoke_check.main()

    assert exit_code == 0
    assert "skip" in capsys.readouterr().out


def test_main_skips_when_connection_fails(monkeypatch, capsys):
    """접속 시도 자체가 실패하면 실패가 아니라 skip하는지 확인한다."""
    monkeypatch.setenv(postgresql_smoke_check.DSN_ENV_VAR, "postgresql://wiki:wiki@localhost/wiki_engine")
    monkeypatch.setattr(postgresql_smoke_check, "_psql_client", lambda: "psql")
    monkeypatch.setattr(postgresql_smoke_check, "check_connection", lambda client, conn: False)

    exit_code = postgresql_smoke_check.main()

    assert exit_code == 0
    assert "skip" in capsys.readouterr().out
