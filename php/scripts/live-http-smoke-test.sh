#!/usr/bin/env bash
# 공개 URL에 대해 실제 HTTP 요청으로 수행하는 배포 후 스모크 테스트.
#
# post-cutover-validate.sh는 아직 계획만 출력하는 골격이지만, 이 스크립트는
# curl로 실제 접속 확인과 민감 경로 노출 점검을 수행한다(0671 acceptance
# criteria: "iowiki.iwinv.net에서 HTTP 접속 smoke test를 수행한다").
set -euo pipefail

BASE_URL=""
declare -a FAILURES=()

SENSITIVE_PATHS=(
  "config/"
  "config/database.php"
  "vendor/"
  "vendor/autoload.php"
  "storage/"
  "storage/installer/install.lock"
  "db/"
  "db/schema/schema.sql"
  "composer.json"
  "composer.lock"
  ".env"
)

usage() {
  cat <<'USAGE'
Usage: php/scripts/live-http-smoke-test.sh --base-url URL

Checks performed:
  - --base-url 자체가 2xx로 응답하는지 확인한다.
  - config/, vendor/, storage/, db/, composer.json, composer.lock, .env 같은
    민감 경로가 403 또는 404로 차단되는지 확인한다(200이면 실패로 표시).

Options:
  --base-url URL   확인할 공개 URL (필수).
  -h, --help       도움말을 출력한다.
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
      echo "Unknown live-http-smoke-test option: $1" >&2
      exit 2
      ;;
  esac
done

if [ "${BASE_URL}" = "" ]; then
  usage >&2
  echo "Missing required option: --base-url" >&2
  exit 2
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl CLI를 찾을 수 없어 smoke test를 실행할 수 없습니다." >&2
  exit 1
fi

status_of() {
  curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "$1"
}

echo "base_url=${BASE_URL}"

root_status="$(status_of "${BASE_URL}/")"
echo "check root: GET ${BASE_URL}/ -> ${root_status}"
case "${root_status}" in
  2*) ;;
  *)
    FAILURES+=("root ${BASE_URL}/ returned ${root_status}, expected 2xx")
    ;;
esac

for path in "${SENSITIVE_PATHS[@]}"; do
  url="${BASE_URL}/${path}"
  status="$(status_of "${url}")"
  echo "check sensitive path: GET ${url} -> ${status}"
  case "${status}" in
    403|404) ;;
    *)
      FAILURES+=("sensitive path ${url} returned ${status}, expected 403 or 404")
      ;;
  esac
done

echo ""
if [ "${#FAILURES[@]}" -eq 0 ]; then
  echo "live_http_smoke_test_status=pass"
  exit 0
fi

echo "live_http_smoke_test_status=fail"
for failure in "${FAILURES[@]}"; do
  echo "FAIL: ${failure}" >&2
done
exit 1
