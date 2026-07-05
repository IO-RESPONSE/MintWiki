#!/usr/bin/env bash
# 스킨(Phase H, 0689-0694) 통합 연기 테스트(smoke test)를 실행한다.
# 상단바 노출, 브랜드색 적용, 문서 액션 탭, 반응형 CSS를 확인한다.
# Direct handler와 로컬 CSS 파일을 사용하여 DB/자격 증명 없이 동작한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$PHP_ROOT/vendor/autoload.php" ]; then
  echo "vendor/autoload.php not found — run 'composer install' from php/ first." >&2
  exit 1
fi

echo "🔍 스킨 통합 연기 테스트 시작..."
echo ""

php "$PHP_ROOT/tests/Http/UiSkinSmokeTest.php"

echo ""
echo "✅ 스킨 통합 연기 테스트 완료!"
