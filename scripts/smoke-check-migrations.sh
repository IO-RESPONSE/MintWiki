#!/usr/bin/env bash
set -euo pipefail

# 마이그레이션 연기 테스트를 실행한다.
# 이 스크립트는 다음을 확인한다:
# - 마이그레이션 파일들의 Python 문법 검증
# - 모든 마이그레이션 적용 가능성
# - 마이그레이션 체인의 연속성
# - 생성된 데이터베이스 스키마 검증

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

echo "🔍 마이그레이션 연기 테스트 시작..."
echo ""

# 마이그레이션 관련 테스트만 실행
"$PYTHON" -m pytest tests/test_migration.py -v --tb=short

echo ""
echo "✅ 마이그레이션 연기 테스트 완료!"
