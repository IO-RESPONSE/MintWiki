#!/usr/bin/env bash
# Phase J(NamuMark 렌더 + 편집 UX + history/discussion, 0704-0712) 통합
# 연기 테스트(smoke test)를 실행한다. NamuMark 렌더 마크업(굵게/링크/표/
# TOC), 편집 화면(요약/미리보기/툴바/문법 도움말), history/discussion
# 렌더링을 확인한다. Direct 컴포넌트 호출과 in-memory repository를
# 사용하여 DB/자격 증명 없이 동작한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$PHP_ROOT/vendor/autoload.php" ]; then
  echo "vendor/autoload.php not found — run 'composer install' from php/ first." >&2
  exit 1
fi

echo "🔍 Phase J 통합 연기 테스트 시작..."
echo ""

php "$PHP_ROOT/tests/Http/UiPhaseJSmokeTest.php"

echo ""
echo "✅ Phase J 통합 연기 테스트 완료!"
