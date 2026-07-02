#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

# 도메인 이식성 경계 검사 (PHP 전환 대비: 도메인 계층에 프레임워크 누수 차단)
"$PYTHON" scripts/check_boundaries.py

# 모듈 계약 manifest 검증 (각 모듈이 필수 계약 필드를 채웠는지 확인)
"$PYTHON" scripts/check_module_manifests.py

scripts/test.sh

if command -v git >/dev/null 2>&1; then
  git diff --check
fi

