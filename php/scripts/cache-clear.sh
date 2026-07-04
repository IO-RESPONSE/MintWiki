#!/usr/bin/env bash
# PHP 공유 호스팅 캐시 비우기 명령 골격.
# 실제 캐시 백엔드 연결과 파일 삭제는 후속 태스크에서 추가한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'USAGE'
Usage: php/scripts/cache-clear.sh [--help]

Clears application cache entries.

This is a command skeleton. It does not delete cache data yet.
USAGE
}

case "${1:-}" in
  "")
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    echo "Unknown cache clear option: $1" >&2
    exit 2
    ;;
esac

echo "cache_clear_status=skeleton"
echo "php_root=$PHP_ROOT"
echo "Cache clear backend integration is intentionally not implemented in this skeleton."
