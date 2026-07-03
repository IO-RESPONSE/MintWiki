#!/usr/bin/env bash
# php/ QA 진입점 — test/static check 명령을 한 곳에 둔다(0430 Notes).
# 정적 분석 도구는 아직 도입 전이므로(docs/php-static-analysis-plan.md,
# 트리거 조건이 성립할 때 별도 잡이 추가) 지금은 테스트 실행만 수행한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "${1:-}" = "--performance-budget" ]; then
  php "$PHP_ROOT/tests/Http/UiPerformanceBudgetTest.php"
else
  "$PHP_ROOT/scripts/test.sh"
fi

# 정적 분석 단계(PHPStan/Psalm)는 docs/php-static-analysis-plan.md의 도입
# 트리거 조건이 성립하면 여기에 추가한다 — 지금은 도구가 없어 생략한다.
