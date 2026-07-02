#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

# 도메인 이식성 경계 검사 (PHP 전환 대비: 도메인 계층에 프레임워크 누수 차단)
"$PYTHON" scripts/check_boundaries.py

# DB 모듈 경계 검사 (도메인이 SQLAlchemy/PDO를 직접 보지 않도록 차단)
"$PYTHON" scripts/check_db_module_boundary.py

# PostgreSQL 전용 SQL feature 금지 목록 검사 (MariaDB 이식 대비)
"$PYTHON" scripts/check_sql_denylist.py

scripts/test.sh

if command -v git >/dev/null 2>&1; then
  git diff --check
fi

