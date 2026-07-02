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

# 모듈 → app 역참조 검사 (UI/API 어댑터 계층으로의 의존을 차단)
"$PYTHON" scripts/check_no_app_import_in_modules.py

# 모듈 계약 manifest 검증 (각 모듈이 필수 계약 필드를 채웠는지 확인)
"$PYTHON" scripts/check_module_manifests.py

scripts/test.sh

# PHP QA는 선택 실행: php CLI가 없으면(=PHP 런타임 도구 미설치) 명확히
# skip 메시지를 남기고 넘어간다(0431 Notes).
PHP_QA_SH="$ROOT_DIR/php/scripts/qa.sh"
if command -v php >/dev/null 2>&1; then
  "$PHP_QA_SH"
else
  echo "php CLI를 찾을 수 없어 PHP QA(php/scripts/qa.sh)를 건너뜁니다." >&2
fi

if command -v git >/dev/null 2>&1; then
  git diff --check
fi

