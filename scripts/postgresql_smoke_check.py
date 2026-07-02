#!/usr/bin/env python3
"""PostgreSQL portable schema smoke 테스트 (선택 실행).

MariaDB 쪽 [scripts/mariadb_smoke_check.py](mariadb_smoke_check.py)와 같은
얕은 확인을 PostgreSQL에 대해서도 반복한다: db/schema/*.sql 을 FK 의존
순서대로 실제 PostgreSQL 서버에 적용해 보고, 11개 테이블이 모두 생성되는지만
확인한다.

MariaDB 스크립트와의 차이: PostgreSQL은 이 저장소가 이미 쓰고 있는 "기존
환경"이므로(docs/postgresql-dsn-compatibility.md), 별도 DSN을 새로 만들지
않고 애플리케이션이 이미 쓰는 ``WIKI_DATABASE_URL``(``.env`` 파일의 같은
키)을 그대로 재사용한다 — 기존 환경과 병행 실행한다.

실행 조건(선택 실행/skip):
- ``WIKI_DATABASE_URL`` 환경 변수(또는 ``.env`` 파일의 같은 키)가 비어
  있으면 접속을 시도하지 않고 곧바로 skip한다.
- ``psql`` CLI 클라이언트가 PATH에 없어도 skip한다.
- 접속 자체가 실패해도 skip한다.

DDL 적용 실패/테이블 존재 확인 실패는 skip이 아니라 실패로 취급하고 종료
코드 1로 끝난다.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "db" / "schema"
ENV_FILE = REPO_ROOT / ".env"
DSN_ENV_VAR = "WIKI_DATABASE_URL"

# scripts/mariadb_smoke_check.py 와 동일한 FK 의존 순서
# (docs/mariadb-migration-smoke-plan.md §2 — db/schema는 두 DB가 공유한다).
SCHEMA_ORDER = [
    "schema_migration.sql",
    "account.sql",
    "document.sql",
    "revision.sql",
    "user_session.sql",
    "acl_rule.sql",
    "acl_namespace_rule.sql",
    "discussion_thread.sql",
    "discussion_comment.sql",
    "audit_event.sql",
    "job.sql",
]

# smoke 실행이 사용하는 격리된 대상 데이터베이스 이름. WIKI_DATABASE_URL이
# 가리키는 실제 애플리케이션 데이터베이스는 건드리지 않는다.
SMOKE_DATABASE = "wiki_engine_postgresql_smoke"

# 데이터베이스 생성/삭제(CREATE DATABASE/DROP DATABASE)는 PostgreSQL 규칙상
# 그 데이터베이스에 접속한 채로는 실행할 수 없으므로, 항상 존재하는
# 유지보수용 데이터베이스에 접속해 수행한다.
ADMIN_DATABASE = "postgres"


def _read_dsn_from_env_file() -> str | None:
    """환경 변수에 없으면 .env 파일에서 WIKI_DATABASE_URL 값을 읽는다."""
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        if key.strip() == DSN_ENV_VAR:
            return value.strip()
    return None


def resolve_dsn() -> str | None:
    """실행에 쓸 PostgreSQL DSN을 찾는다(환경 변수 우선, 없으면 .env 파일)."""
    return os.environ.get(DSN_ENV_VAR) or _read_dsn_from_env_file()


def parse_dsn(dsn: str) -> dict:
    """``postgresql://user:pass@host:port/dbname`` 형식 DSN을 분해한다."""
    parsed = urlparse(dsn)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") or "",
    }


def _psql_client() -> str | None:
    """사용 가능한 PostgreSQL CLI 클라이언트 이름을 찾는다."""
    return shutil.which("psql")


def _run_psql(client: str, conn: dict, *, database: str, sql: str | None = None, sql_file: Path | None = None) -> subprocess.CompletedProcess:
    """psql CLI를 호출해 SQL 문자열/파일을 실행한다."""
    args = [
        client,
        f"--host={conn['host']}",
        f"--port={conn['port']}",
        f"--username={conn['user']}",
        f"--dbname={database}",
        "--no-psqlrc",
        "--variable=ON_ERROR_STOP=1",
    ]
    env = {**os.environ, "PGPASSWORD": conn["password"]}
    if sql is not None:
        # 헤더/행 개수 안내 없이 결과 값만 받도록 tuples-only + unaligned 출력을 쓴다.
        args.extend(["--tuples-only", "--no-align", "-c", sql])
        return subprocess.run(args, capture_output=True, text=True, timeout=30, env=env)
    args.extend(["-f", str(sql_file)])
    return subprocess.run(args, capture_output=True, text=True, timeout=60, env=env)


def check_connection(client: str, conn: dict) -> bool:
    """접속 가능 여부를 확인한다."""
    result = _run_psql(client, conn, database=ADMIN_DATABASE, sql="SELECT 1")
    return result.returncode == 0


def prepare_smoke_database(client: str, conn: dict) -> None:
    """smoke 전용 데이터베이스를 새로 만든다."""
    _run_psql(client, conn, database=ADMIN_DATABASE, sql=f"DROP DATABASE IF EXISTS {SMOKE_DATABASE}")
    result = _run_psql(client, conn, database=ADMIN_DATABASE, sql=f"CREATE DATABASE {SMOKE_DATABASE}")
    if result.returncode != 0:
        raise RuntimeError(f"smoke 데이터베이스 생성 실패: {result.stderr.strip()}")


def apply_schema_files(client: str, conn: dict) -> None:
    """db/schema/*.sql 을 FK 의존 순서대로 그대로 적용한다."""
    for filename in SCHEMA_ORDER:
        sql_file = SCHEMA_DIR / filename
        result = _run_psql(client, conn, database=SMOKE_DATABASE, sql_file=sql_file)
        if result.returncode != 0:
            raise RuntimeError(f"DDL 적용 실패 ({filename}): {result.stderr.strip()}")


def verify_tables_exist(client: str, conn: dict) -> None:
    """11개 테이블이 모두 생성됐는지 카탈로그 조회로 확인한다."""
    result = _run_psql(
        client,
        conn,
        database=SMOKE_DATABASE,
        sql=(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        ),
    )
    if result.returncode != 0:
        raise RuntimeError(f"테이블 존재 확인 조회 실패: {result.stderr.strip()}")

    # --tuples-only 이므로 헤더/행 개수 안내 없이 값 라인만 온다.
    existing = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    expected = {name.removesuffix(".sql") for name in SCHEMA_ORDER}
    missing = expected - existing
    if missing:
        raise RuntimeError(f"테이블 존재 확인 실패: 생성되지 않은 테이블 {sorted(missing)}")


def cleanup_smoke_database(client: str, conn: dict) -> None:
    """반복 실행이 항상 깨끗하게 시작하도록 smoke 데이터베이스를 삭제한다."""
    _run_psql(client, conn, database=ADMIN_DATABASE, sql=f"DROP DATABASE IF EXISTS {SMOKE_DATABASE}")


def _skip(message: str) -> int:
    print(f"⏭  PostgreSQL smoke 테스트 skip: {message}")
    return 0


def main() -> int:
    dsn = resolve_dsn()
    if not dsn:
        return _skip(f"{DSN_ENV_VAR} 이 설정되지 않았습니다")

    client = _psql_client()
    if client is None:
        return _skip("psql CLI 클라이언트를 찾을 수 없습니다")

    conn = parse_dsn(dsn)

    if not check_connection(client, conn):
        return _skip(f"{conn['host']}:{conn['port']} 접속에 실패했습니다")

    try:
        prepare_smoke_database(client, conn)
        apply_schema_files(client, conn)
        verify_tables_exist(client, conn)
    except RuntimeError as exc:
        print(f"❌ PostgreSQL smoke 테스트 실패: {exc}", file=sys.stderr)
        return 1
    finally:
        cleanup_smoke_database(client, conn)

    print("✅ PostgreSQL smoke 테스트 통과: 11개 테이블 모두 생성 확인")
    return 0


if __name__ == "__main__":
    sys.exit(main())
