#!/usr/bin/env bash
# UI route 연기 테스트(smoke test)를 실행한다.
# 이 스크립트는 UiRoutes 등록과 응답 계약을 검증한다.
# Direct handler를 사용하여 네트워크 의존 없이 동작한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$PHP_ROOT/vendor/autoload.php" ]; then
  echo "vendor/autoload.php not found — run 'composer install' from php/ first." >&2
  exit 1
fi

echo "🔍 UI route 연기 테스트 시작..."
echo ""

php "$PHP_ROOT/tests/Http/UiRoutesTest.php"

echo ""
echo "✅ UI route 연기 테스트 완료!"
