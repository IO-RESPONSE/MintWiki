#!/usr/bin/env bash
# UI form 연기 테스트(smoke test)를 실행한다.
# 이 스크립트는 문서 생성/편집 form의 CSRF 토큰 흐름을 검증한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$PHP_ROOT/vendor/autoload.php" ]; then
  echo "vendor/autoload.php not found — run 'composer install' from php/ first." >&2
  exit 1
fi

echo "🔍 UI form 연기 테스트 시작..."
echo ""

php "$PHP_ROOT/tests/Http/UiFormSmokeTest.php"

echo ""
echo "✅ UI form 연기 테스트 완료!"
