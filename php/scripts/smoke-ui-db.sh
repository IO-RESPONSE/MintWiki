#!/usr/bin/env bash
# UI DB 연기 테스트(smoke test)를 실행한다.
# 이 스크립트는 문서 생성/조회 DB round-trip을 검증한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$PHP_ROOT/vendor/autoload.php" ]; then
  echo "vendor/autoload.php not found — run 'composer install' from php/ first." >&2
  exit 1
fi

echo "🔍 UI DB 연기 테스트 시작..."
echo ""

php "$PHP_ROOT/tests/Http/UiDbSmokeTest.php"

echo ""
echo "✅ UI DB 연기 테스트 완료!"
