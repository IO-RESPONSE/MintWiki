#!/usr/bin/env python3
"""MariaDB portable schema smoke 테스트 (선택 실행).

docs/mariadb-migration-smoke-plan.md가 세운 계획을 그대로 구현한다:
db/schema/*.sql 을 FK 의존 순서대로 실제 MariaDB 서버에 적용해 보고, 12개
테이블이 모두 생성되는지만 확인하는 가장 얕은 확인이다.

실행 조건(선택 실행/skip):
- ``WIKI_MARIADB_DSN`` 환경 변수(또는 ``.env`` 파일의 같은 키)가 비어 있으면
  접속을 시도하지 않고 곧바로 skip한다.
- ``mysql`` CLI 클라이언트가 PATH에 없어도 skip한다.
- 접속 자체가 실패해도 skip한다(§1, §4 "접속 실패 → skip").

DDL 적용 실패/테이블 존재 확인 실패는 skip이 아니라 실패로 취급하고 종료
코드 1로 끝난다(§4).
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
DSN_ENV_VAR = "WIKI_MARIADB_DSN"

# docs/mariadb-migration-smoke-plan.md §2 가 정한 FK 의존 순서.
SCHEMA_ORDER = [
    "schema_migration.sql",
    "schema_version.sql",
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

# smoke 실행이 사용하는 격리된 대상 스키마 이름. 운영 DSN이 가리키는
# 데이터베이스는 건드리지 않는다(§3의 2단계).
SMOKE_DATABASE = "wiki_engine_mariadb_smoke"


def _read_dsn_from_env_file() -> str | None:
    """환경 변수에 없으면 .env 파일에서 WIKI_MARIADB_DSN 값을 읽는다."""
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
    """실행에 쓸 MariaDB DSN을 찾는다(환경 변수 우선, 없으면 .env 파일)."""
    return os.environ.get(DSN_ENV_VAR) or _read_dsn_from_env_file()


def parse_dsn(dsn: str) -> dict:
    """``mysql+pymysql://user:pass@host:port/dbname`` 형식 DSN을 분해한다."""
    parsed = urlparse(dsn)
    return {
        "user": parsed.username or "root",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "database": parsed.path.lstrip("/") or "",
    }


def _mysql_client() -> str | None:
    """사용 가능한 MariaDB/MySQL CLI 클라이언트 이름을 찾는다."""
    for candidate in ("mariadb", "mysql"):
        if shutil.which(candidate):
            return candidate
    return None


def _run_mysql(client: str, conn: dict, *, database: str | None = None, sql: str | None = None, sql_file: Path | None = None) -> subprocess.CompletedProcess:
    """mysql CLI를 호출해 SQL 문자열/파일을 실행한다."""
    args = [
        client,
        f"--host={conn['host']}",
        f"--port={conn['port']}",
        f"--user={conn['user']}",
    ]
    if conn["password"]:
        args.append(f"--password={conn['password']}")
    if database:
        args.append(database)
    if sql is not None:
        args.extend(["-e", sql])
        return subprocess.run(args, capture_output=True, text=True, timeout=30)
    with open(sql_file, "rb") as fh:
        return subprocess.run(args, stdin=fh, capture_output=True, text=True, timeout=60)


def check_connection(client: str, conn: dict) -> bool:
    """접속 가능 여부를 확인한다(§3 1단계)."""
    result = _run_mysql(client, conn, sql="SELECT 1")
    return result.returncode == 0


def prepare_smoke_database(client: str, conn: dict) -> None:
    """smoke 전용 데이터베이스를 새로 만든다(§3 2단계)."""
    _run_mysql(client, conn, sql=f"DROP DATABASE IF EXISTS {SMOKE_DATABASE}")
    result = _run_mysql(client, conn, sql=f"CREATE DATABASE {SMOKE_DATABASE}")
    if result.returncode != 0:
        raise RuntimeError(f"smoke 데이터베이스 생성 실패: {result.stderr.strip()}")


def apply_schema_files(client: str, conn: dict) -> None:
    """db/schema/*.sql 을 FK 의존 순서대로 그대로 적용한다(§3 3단계)."""
    for filename in SCHEMA_ORDER:
        sql_file = SCHEMA_DIR / filename
        result = _run_mysql(client, conn, database=SMOKE_DATABASE, sql_file=sql_file)
        if result.returncode != 0:
            raise RuntimeError(f"DDL 적용 실패 ({filename}): {result.stderr.strip()}")


def verify_tables_exist(client: str, conn: dict) -> None:
    """11개 테이블이 모두 생성됐는지 카탈로그 조회로 확인한다(§3 4단계)."""
    result = _run_mysql(
        client,
        conn,
        database=SMOKE_DATABASE,
        sql=(
            "SELECT table_name FROM information_schema.tables "
            f"WHERE table_schema = '{SMOKE_DATABASE}'"
        ),
    )
    if result.returncode != 0:
        raise RuntimeError(f"테이블 존재 확인 조회 실패: {result.stderr.strip()}")

    existing = {line.strip() for line in result.stdout.splitlines()[1:] if line.strip()}
    expected = {name.removesuffix(".sql") for name in SCHEMA_ORDER}
    missing = expected - existing
    if missing:
        raise RuntimeError(f"테이블 존재 확인 실패: 생성되지 않은 테이블 {sorted(missing)}")


def cleanup_smoke_database(client: str, conn: dict) -> None:
    """반복 실행이 항상 깨끗하게 시작하도록 smoke 데이터베이스를 삭제한다(§3 5단계, §5)."""
    _run_mysql(client, conn, sql=f"DROP DATABASE IF EXISTS {SMOKE_DATABASE}")


def _skip(message: str) -> int:
    print(f"⏭  MariaDB smoke 테스트 skip: {message}")
    return 0


def main() -> int:
    dsn = resolve_dsn()
    if not dsn:
        return _skip(f"{DSN_ENV_VAR} 이 설정되지 않았습니다")

    client = _mysql_client()
    if client is None:
        return _skip("mysql/mariadb CLI 클라이언트를 찾을 수 없습니다")

    conn = parse_dsn(dsn)

    if not check_connection(client, conn):
        return _skip(f"{conn['host']}:{conn['port']} 접속에 실패했습니다")

    try:
        prepare_smoke_database(client, conn)
        apply_schema_files(client, conn)
        verify_tables_exist(client, conn)
    except RuntimeError as exc:
        print(f"❌ MariaDB smoke 테스트 실패: {exc}", file=sys.stderr)
        return 1
    finally:
        cleanup_smoke_database(client, conn)

    print("✅ MariaDB smoke 테스트 통과: 12개 테이블 모두 생성 확인")
    return 0


if __name__ == "__main__":
    sys.exit(main())
