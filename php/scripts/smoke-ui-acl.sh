#!/usr/bin/env bash
# UI ACL 연기 테스트(smoke test)를 실행한다.
# 이 스크립트는 권한 거부 결정의 상태를 검증한다.
# Direct handler를 사용하여 네트워크 의존 없이 동작한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$PHP_ROOT/vendor/autoload.php" ]; then
  echo "vendor/autoload.php not found — run 'composer install' from php/ first." >&2
  exit 1
fi

echo "🔍 UI ACL 연기 테스트 시작..."
echo ""

php "$PHP_ROOT/tests/Http/UiAclSmokeTest.php"

echo ""
echo "✅ UI ACL 연기 테스트 완료!"
