#!/usr/bin/env bash
# Phase K(삭제 + 감사 로그 + 백업 다운로드 + 진단, 0714-0717) 통합 연기
# 테스트(smoke test)를 실행한다. 문서 삭제 확인 화면, 실제 감사 이벤트
# 렌더링, 백업 다운로드 링크/traversal 거부, 운영 진단 실데이터+export 민감
# 정보 제외를 확인한다. Direct 컴포넌트 호출과 임시 디렉터리를 사용하여
# DB/자격 증명 없이 동작한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$PHP_ROOT/vendor/autoload.php" ]; then
  echo "vendor/autoload.php not found — run 'composer install' from php/ first." >&2
  exit 1
fi

echo "🔍 Phase K 통합 연기 테스트 시작..."
echo ""

php "$PHP_ROOT/tests/Http/UiPhaseKSmokeTest.php"

echo ""
echo "✅ Phase K 통합 연기 테스트 완료!"
