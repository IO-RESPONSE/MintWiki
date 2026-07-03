#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

# PHP + MariaDB packaging gate: portable SQL과 PHP 런타임을 기본 검증한다.
#
# 기존 Python 엔진은 참조 구현으로 남아 있지만, 새 main 후보의 기본 산출물은
# php/ 런타임과 db/schema portable SQL이다. Python 전체 테스트는 아래
# RUN_PYTHON_REFERENCE_QA=1 옵션으로 별도 실행한다.

# DB 모듈 경계 검사 (도메인이 SQLAlchemy/PDO를 직접 보지 않도록 차단)
"$PYTHON" scripts/check_db_module_boundary.py

# PostgreSQL 전용 SQL feature 금지 목록 검사 (MariaDB 이식 대비)
"$PYTHON" scripts/check_sql_denylist.py

"$PYTHON" scripts/schema_compatibility_report.py >/dev/null

PHP_QA_SH="$ROOT_DIR/php/scripts/qa.sh"
if command -v php >/dev/null 2>&1; then
  "$PHP_QA_SH" "$@"
else
  echo "php CLI를 찾을 수 없어 PHP/MariaDB 패키징 QA를 실행할 수 없습니다." >&2
  exit 1
fi

if [ "${RUN_PYTHON_REFERENCE_QA:-0}" = "1" ]; then
  "$PYTHON" scripts/check_boundaries.py
  "$PYTHON" scripts/check_no_app_import_in_modules.py
  "$PYTHON" scripts/check_module_manifests.py
  scripts/test.sh
fi

if command -v git >/dev/null 2>&1; then
  git diff --check
fi
