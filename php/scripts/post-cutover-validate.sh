#!/usr/bin/env bash
# PHP cutover 이후 검증 절차의 CLI 골격.
# 실제 HTTP 요청, DB 진단, 문서 생성/조회 자동화는 후속 태스크에서 연결한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL=""

usage() {
  cat <<'USAGE'
Usage: php/scripts/post-cutover-validate.sh [--base-url URL] [--help]

Prints the post-cutover validation plan.

Checks covered by this skeleton:
  health           GET /health
  db               DB connection and schema readiness
  document_create  Create a validation document
  document_view    View the validation document

This is a command skeleton. It does not send HTTP requests or write documents yet.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --base-url)
      if [ "${2:-}" = "" ]; then
        usage >&2
        echo "Missing value for --base-url" >&2
        exit 2
      fi
      BASE_URL="${2%/}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      echo "Unknown post-cutover validation option: $1" >&2
      exit 2
      ;;
  esac
done

if [ "$BASE_URL" = "" ]; then
  BASE_URL="https://example.invalid"
fi

cat <<EOF
post_cutover_validation_status=skeleton
php_root=$PHP_ROOT
base_url=$BASE_URL
checks:
  health: GET $BASE_URL/health
  db: verify DB connection and schema readiness
  document_create: POST $BASE_URL/documents
  document_view: GET $BASE_URL/documents/{created-document}
HTTP requests, DB probes, and document writes are intentionally not implemented in this skeleton.
EOF
