#!/usr/bin/env bash
# php/tests/ 아래 모든 *Test.php 를 순회 실행하는 통합 테스트 러너.
# docs/php-test-bootstrap.md 가 예고한 0430 산출물 — 각 테스트 파일은
# 외부 프레임워크 없이 `php` CLI로 직접 실행되고 exit(0)/exit(1)로
# 성공/실패를 알린다(docs/php-test-bootstrap.md).
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PHP_ROOT"

if [ ! -f "vendor/autoload.php" ]; then
  echo "vendor/autoload.php not found — run 'composer install' from php/ first." >&2
  exit 1
fi

failures=0
total=0

while IFS= read -r -d '' test_file; do
  total=$((total + 1))
  relative_path="${test_file#"$PHP_ROOT"/}"
  if php "$test_file" > /tmp/php-test-output.$$ 2>&1; then
    echo "PASS $relative_path"
  else
    failures=$((failures + 1))
    echo "FAIL $relative_path"
    cat /tmp/php-test-output.$$ >&2
  fi
  rm -f /tmp/php-test-output.$$
done < <(find tests -name '*Test.php' -print0 | sort -z)

echo "---"
echo "$((total - failures))/$total passed"

if [ "$failures" -gt 0 ]; then
  exit 1
fi
