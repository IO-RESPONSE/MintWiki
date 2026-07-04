#!/usr/bin/env bash
# 라이브 호스팅 배포본에 대한 API/HTTP 기반 end-to-end smoke test (태스크 0672).
#
# post-cutover-validate.sh(골격)나 live-http-smoke-test.sh(루트 응답/민감
# 경로 차단만 확인)와 달리, 이 스크립트는 관리자/일반 사용자/읽기 전용
# 사용자/익명 사용자 네 종류의 세션으로 실제 로그인, 문서 생성/수정/삭제,
# 계정 생성, 권한 거부 흐름을 curl로 직접 수행하고 결과를 기록한다.
#
# 이 저장소의 PHP 프런트 컨트롤러(php/public/index.php)는 현재
# `GET /`와 `GET /health`만 실제로 연결되어 있고, 로그인/문서/관리자 관련
# route들(php/src/Http/*Routes.php)은 아직 프런트 컨트롤러에 연결되지
# 않았다(0673+ 대상). 이 스크립트는 그 상태에서도 안전하게 실행되도록,
# 각 시나리오가 차단(blocked)되면 나머지를 스킵하고 이유를 기록한 뒤
# 계속 진행한다 — 실패/차단 시나리오를 이유와 함께 남기는 것이 이
# 태스크의 목적이다("실패한 시나리오는 0673+로 넘긴다").
set -uo pipefail

BASE_URL=""
KEEP_DATA=0

usage() {
  cat <<'USAGE'
Usage: php/scripts/live-e2e-smoke-test.sh --base-url URL [options]

라이브 배포본에 대해 아래 순서로 실제 HTTP 요청을 보내고 결과를 기록한다:
  1. GET /health 로 배포 상태를 확인한다(전제 조건).
  2. 관리자 계정 생성 또는 로그인(SMOKE_ADMIN_USER/SMOKE_ADMIN_PASSWORD).
  3. 관리자 세션으로 테스트 문서 생성/수정/삭제(또는 숨김) 시도.
  4. 관리자 세션으로 일반 사용자 계정, 읽기 전용 사용자 계정 생성 시도.
  5. 일반 사용자 로그인 후 문서 생성/편집 허용 여부 확인.
  6. 읽기 전용 사용자 로그인 후 읽기 가능/쓰기 거부 여부 확인.
  7. 익명 사용자로 공개 페이지 읽기 확인.
  8. 생성한 데이터 정리를 시도하고, 정리하지 못한 데이터를 기록한다.

각 단계는 실패해도 스크립트를 중단하지 않는다 — 라우트가 아직 연결되지
않았거나(404) 기능이 아직 없으면 "blocked"로 기록하고 다음 단계로
넘어간다. 계정 생성에 실패하면 그 계정에 의존하는 이후 단계는
"skip"으로 기록된다.

Options:
  --base-url URL           확인할 공개 URL (필수).
  --keep-data               정리(cleanup) 단계를 건너뛴다(디버깅용).
  -h, --help                 도움말을 출력한다.

환경변수(선택, 값은 출력/로그에 남기지 않는다):
  SMOKE_ADMIN_USER, SMOKE_ADMIN_PASSWORD   0671에서 만든 기존 관리자 계정.
                                             비어 있으면 새 관리자 계정 생성을
                                             먼저 시도한다.

테스트 계정 이름은 smoke_admin_*, smoke_user_*, smoke_readonly_* 접두사를,
테스트 문서 제목은 SmokeTest-YYYYMMDD-HHMMSS-* 접두사를 사용한다.
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
    --keep-data)
      KEEP_DATA=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      echo "Unknown live-e2e-smoke-test option: $1" >&2
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

RUN_ID="$(date +%Y%m%d-%H%M%S)"
DOC_PREFIX="SmokeTest-${RUN_ID}"
ADMIN_USER_NAME="${SMOKE_ADMIN_USER:-}"
ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-}"
NEW_ADMIN_USER_NAME="smoke_admin_${RUN_ID}"
NORMAL_USER_NAME="smoke_user_${RUN_ID}"
READONLY_USER_NAME="smoke_readonly_${RUN_ID}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "${WORKDIR}"' EXIT

ADMIN_JAR="${WORKDIR}/admin-cookies.txt"
USER_JAR="${WORKDIR}/user-cookies.txt"
READONLY_JAR="${WORKDIR}/readonly-cookies.txt"
ANON_JAR="${WORKDIR}/anon-cookies.txt"

PASS_COUNT=0
FAIL_COUNT=0
BLOCKED_COUNT=0
SKIP_COUNT=0
declare -a LEFTOVER_NOTES=()

# 시나리오 결과 한 줄을 기록하고 요약 카운터를 갱신한다.
record() {
  local verdict="$1" name="$2" method="$3" url="$4" status="$5" redirect="$6" note="$7"
  echo "[${verdict}] ${name}: ${method} ${url} -> status=${status} redirect=${redirect:-none} ${note}"
  case "${verdict}" in
    pass) PASS_COUNT=$((PASS_COUNT + 1)) ;;
    fail) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    blocked) BLOCKED_COUNT=$((BLOCKED_COUNT + 1)) ;;
    skip) SKIP_COUNT=$((SKIP_COUNT + 1)) ;;
  esac
}

# GET 요청을 보내고 LAST_STATUS/LAST_BODY_FILE/LAST_REDIRECT를 채운다.
http_get() {
  local url="$1" jar="$2"
  local body_file header_file
  body_file="$(mktemp "${WORKDIR}/body.XXXXXX")"
  header_file="$(mktemp "${WORKDIR}/header.XXXXXX")"
  LAST_STATUS="$(curl -sS -m 15 -c "${jar}" -b "${jar}" -D "${header_file}" -o "${body_file}" -w '%{http_code}' "${url}" 2>/dev/null)"
  if [ -z "${LAST_STATUS}" ]; then
    LAST_STATUS="000"
  fi
  LAST_BODY_FILE="${body_file}"
  LAST_REDIRECT="$(grep -i '^Location:' "${header_file}" 2>/dev/null | tail -1 | tr -d '\r' | sed 's/^[Ll]ocation: *//')"
}

# form-urlencoded POST 요청을 보낸다. 필드는 "name=value" 인자로 전달하며,
# 값은 curl config(-K -)로 표준입력을 통해서만 전달되어 프로세스 목록(ps)에
# 비밀번호가 노출되지 않는다.
http_post_form() {
  local url="$1" jar="$2"; shift 2
  local body_file header_file config_file
  body_file="$(mktemp "${WORKDIR}/body.XXXXXX")"
  header_file="$(mktemp "${WORKDIR}/header.XXXXXX")"
  config_file="$(mktemp "${WORKDIR}/curlcfg.XXXXXX")"

  {
    printf 'url = "%s"\n' "${url}"
    printf 'request = "POST"\n'
    for field in "$@"; do
      printf 'data-urlencode = "%s"\n' "${field}"
    done
  } > "${config_file}"

  LAST_STATUS="$(curl -sS -m 15 -c "${jar}" -b "${jar}" -D "${header_file}" -o "${body_file}" -w '%{http_code}' -K "${config_file}" 2>/dev/null)"
  if [ -z "${LAST_STATUS}" ]; then
    LAST_STATUS="000"
  fi
  LAST_BODY_FILE="${body_file}"
  LAST_REDIRECT="$(grep -i '^Location:' "${header_file}" 2>/dev/null | tail -1 | tr -d '\r' | sed 's/^[Ll]ocation: *//')"
}

# HTML body에서 hidden csrf_token 필드 값을 추출한다. 없으면 빈 문자열.
extract_csrf_token() {
  local file="$1"
  grep -o 'name="csrf_token" value="[^"]*"' "${file}" 2>/dev/null | head -1 | sed 's/.*value="//; s/"$//'
}

# 지정한 페이지를 새로 조회해 최신 csrf_token 값을 반환한다.
fresh_csrf_token() {
  local url="$1" jar="$2"
  http_get "${url}" "${jar}"
  extract_csrf_token "${LAST_BODY_FILE}"
}

random_password() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 16
  else
    head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'
  fi
}

echo "base_url=${BASE_URL}"
echo "run_id=${RUN_ID}"
echo "doc_prefix=${DOC_PREFIX}"
echo ""

# 0. 배포 상태 전제 조건 확인: /health
http_get "${BASE_URL}/health" "${ANON_JAR}"
APP_REACHABLE=0
case "${LAST_STATUS}" in
  200)
    if grep -q '"status"[[:space:]]*:[[:space:]]*"ok"' "${LAST_BODY_FILE}" 2>/dev/null; then
      APP_REACHABLE=1
      record pass health_check GET "${BASE_URL}/health" "${LAST_STATUS}" "${LAST_REDIRECT}" "app reachable"
    else
      record fail health_check GET "${BASE_URL}/health" "${LAST_STATUS}" "${LAST_REDIRECT}" "unexpected body"
    fi
    ;;
  *)
    record blocked health_check GET "${BASE_URL}/health" "${LAST_STATUS}" "${LAST_REDIRECT}" "app not deployed yet or /health unreachable"
    ;;
esac

# 1. 익명 사용자 공개 페이지 읽기 확인 (홈페이지 — 별도 공개 문서 read
#    route가 아직 없으므로 GET / 을 대상으로 한다).
http_get "${BASE_URL}/" "${ANON_JAR}"
case "${LAST_STATUS}" in
  2*) record pass anonymous_read_home GET "${BASE_URL}/" "${LAST_STATUS}" "${LAST_REDIRECT}" "public home page readable" ;;
  *) record fail anonymous_read_home GET "${BASE_URL}/" "${LAST_STATUS}" "${LAST_REDIRECT}" "expected 2xx" ;;
esac

ADMIN_AUTHENTICATED=0
ADMIN_LOGIN_USER=""

if [ "${APP_REACHABLE}" -ne 1 ]; then
  record blocked admin_login_or_create GET/POST "${BASE_URL}/login" "n/a" "" "skipped: /health precondition failed"
elif [ -n "${ADMIN_USER_NAME}" ] && [ -n "${ADMIN_PASSWORD}" ]; then
  # 2a. 0671에서 만든 기존 관리자 계정으로 로그인 시도.
  http_get "${BASE_URL}/login" "${ADMIN_JAR}"
  if [ "${LAST_STATUS}" = "200" ]; then
    token="$(extract_csrf_token "${LAST_BODY_FILE}")"
    http_post_form "${BASE_URL}/login" "${ADMIN_JAR}" "username=${ADMIN_USER_NAME}" "password=${ADMIN_PASSWORD}" "csrf_token=${token}"
    case "${LAST_STATUS}" in
      200|302)
        ADMIN_AUTHENTICATED=1
        ADMIN_LOGIN_USER="${ADMIN_USER_NAME}"
        record pass admin_login POST "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "logged in as existing admin account"
        ;;
      *)
        record fail admin_login POST "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "login rejected for existing admin account"
        ;;
    esac
  else
    record blocked admin_login GET "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "login form route not available"
  fi
else
  # 2b. 관리자 계정이 제공되지 않았으므로 설치 마법사(installer)를 통한
  #     신규 관리자 계정 생성을 시도한다.
  http_get "${BASE_URL}/install" "${ADMIN_JAR}"
  if [ "${LAST_STATUS}" = "200" ]; then
    token="$(extract_csrf_token "${LAST_BODY_FILE}")"
    generated_password="$(random_password)"
    http_post_form "${BASE_URL}/install" "${ADMIN_JAR}" "username=${NEW_ADMIN_USER_NAME}" "password=${generated_password}" "csrf_token=${token}"
    case "${LAST_STATUS}" in
      200|302)
        ADMIN_AUTHENTICATED=1
        ADMIN_LOGIN_USER="${NEW_ADMIN_USER_NAME}"
        record pass admin_login_or_create POST "${BASE_URL}/install" "${LAST_STATUS}" "${LAST_REDIRECT}" "created admin account ${NEW_ADMIN_USER_NAME} via installer"
        ;;
      *)
        record fail admin_login_or_create POST "${BASE_URL}/install" "${LAST_STATUS}" "${LAST_REDIRECT}" "installer admin account step rejected the submission"
        ;;
    esac
  else
    record blocked admin_login_or_create GET "${BASE_URL}/install" "${LAST_STATUS}" "${LAST_REDIRECT}" "no SMOKE_ADMIN_USER/SMOKE_ADMIN_PASSWORD given and /install unavailable (already installed or route not wired)"
  fi
fi

DOC_ID=""
DOC_TITLE="${DOC_PREFIX}-doc"

if [ "${ADMIN_AUTHENTICATED}" -ne 1 ]; then
  record skip admin_create_document POST "${BASE_URL}/documents" "n/a" "" "skipped: no authenticated admin session"
else
  # 3. 관리자 세션에서 테스트 문서 생성.
  http_get "${BASE_URL}/documents/new" "${ADMIN_JAR}"
  if [ "${LAST_STATUS}" = "200" ]; then
    token="$(extract_csrf_token "${LAST_BODY_FILE}")"
    http_post_form "${BASE_URL}/documents" "${ADMIN_JAR}" "title=${DOC_TITLE}" "source=smoke test body ${RUN_ID}" "csrf_token=${token}"
    case "${LAST_STATUS}" in
      200|201|302)
        DOC_ID="$(grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' "${LAST_BODY_FILE}" 2>/dev/null | head -1 | sed 's/.*:[[:space:]]*"//; s/"$//')"
        if [ -z "${DOC_ID}" ] && [ -n "${LAST_REDIRECT}" ]; then
          DOC_ID="$(basename "${LAST_REDIRECT}")"
        fi
        record pass admin_create_document POST "${BASE_URL}/documents" "${LAST_STATUS}" "${LAST_REDIRECT}" "created document title=${DOC_TITLE} id=${DOC_ID:-unknown}"
        ;;
      *)
        record fail admin_create_document POST "${BASE_URL}/documents" "${LAST_STATUS}" "${LAST_REDIRECT}" "document create rejected"
        ;;
    esac
  else
    record blocked admin_create_document GET "${BASE_URL}/documents/new" "${LAST_STATUS}" "${LAST_REDIRECT}" "document create form route not available"
  fi
fi

if [ -z "${DOC_ID}" ]; then
  record skip admin_edit_document POST "${BASE_URL}/documents/{id}" "n/a" "" "skipped: no document id from create step"
else
  # 4. 관리자 세션에서 테스트 문서 수정.
  http_get "${BASE_URL}/documents/${DOC_ID}/edit" "${ADMIN_JAR}"
  if [ "${LAST_STATUS}" = "200" ]; then
    token="$(extract_csrf_token "${LAST_BODY_FILE}")"
    http_post_form "${BASE_URL}/documents/${DOC_ID}" "${ADMIN_JAR}" "title=${DOC_TITLE}-edited" "source=smoke test body edited ${RUN_ID}" "csrf_token=${token}"
    case "${LAST_STATUS}" in
      200|302) record pass admin_edit_document POST "${BASE_URL}/documents/${DOC_ID}" "${LAST_STATUS}" "${LAST_REDIRECT}" "edited document" ;;
      *) record fail admin_edit_document POST "${BASE_URL}/documents/${DOC_ID}" "${LAST_STATUS}" "${LAST_REDIRECT}" "document edit rejected" ;;
    esac
  else
    record blocked admin_edit_document GET "${BASE_URL}/documents/${DOC_ID}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "document edit form route not available"
  fi
fi

DOC_DELETED=0
if [ -z "${DOC_ID}" ]; then
  record skip admin_delete_or_hide_document POST "${BASE_URL}/documents/{id}/delete" "n/a" "" "skipped: no document id from create step"
else
  # 5. 관리자 세션에서 테스트 문서 삭제(불가하면 숨김/보호 상태로 전환).
  delete_token="$(fresh_csrf_token "${BASE_URL}/documents/${DOC_ID}/edit" "${ADMIN_JAR}")"
  http_post_form "${BASE_URL}/documents/${DOC_ID}/delete" "${ADMIN_JAR}" "csrf_token=${delete_token}"
  case "${LAST_STATUS}" in
    200|204|302)
      DOC_DELETED=1
      record pass admin_delete_or_hide_document POST "${BASE_URL}/documents/${DOC_ID}/delete" "${LAST_STATUS}" "${LAST_REDIRECT}" "document deleted"
      ;;
    *)
      # 삭제 route가 없으면 숨김 상태 전환을 대신 시도한다.
      hide_token="$(fresh_csrf_token "${BASE_URL}/documents/${DOC_ID}/edit" "${ADMIN_JAR}")"
      http_post_form "${BASE_URL}/documents/${DOC_ID}" "${ADMIN_JAR}" "status=hidden" "csrf_token=${hide_token}"
      case "${LAST_STATUS}" in
        200|302)
          DOC_DELETED=1
          record pass admin_delete_or_hide_document POST "${BASE_URL}/documents/${DOC_ID}" "${LAST_STATUS}" "${LAST_REDIRECT}" "document hidden instead of deleted"
          ;;
        *)
          record blocked admin_delete_or_hide_document POST "${BASE_URL}/documents/${DOC_ID}/delete" "${LAST_STATUS}" "${LAST_REDIRECT}" "no delete or hide route available"
          LEFTOVER_NOTES+=("document id=${DOC_ID} title=${DOC_TITLE} could not be deleted or hidden")
          ;;
      esac
      ;;
  esac
fi

NORMAL_USER_CREATED=0
if [ "${ADMIN_AUTHENTICATED}" -ne 1 ]; then
  record skip admin_create_normal_user POST "${BASE_URL}/admin/users" "n/a" "" "skipped: no authenticated admin session"
else
  # 6. 관리자 세션에서 일반 사용자 계정 생성.
  NORMAL_USER_PASSWORD="$(random_password)"
  http_get "${BASE_URL}/admin/users/new" "${ADMIN_JAR}"
  token="$(extract_csrf_token "${LAST_BODY_FILE}")"
  http_post_form "${BASE_URL}/admin/users" "${ADMIN_JAR}" "username=${NORMAL_USER_NAME}" "password=${NORMAL_USER_PASSWORD}" "role=user" "csrf_token=${token}"
  case "${LAST_STATUS}" in
    200|201|302)
      NORMAL_USER_CREATED=1
      record pass admin_create_normal_user POST "${BASE_URL}/admin/users" "${LAST_STATUS}" "${LAST_REDIRECT}" "created ${NORMAL_USER_NAME}"
      ;;
    *)
      record blocked admin_create_normal_user POST "${BASE_URL}/admin/users" "${LAST_STATUS}" "${LAST_REDIRECT}" "user creation route not available"
      ;;
  esac
fi

READONLY_USER_CREATED=0
if [ "${ADMIN_AUTHENTICATED}" -ne 1 ]; then
  record skip admin_create_readonly_user POST "${BASE_URL}/admin/users" "n/a" "" "skipped: no authenticated admin session"
else
  # 7. 관리자 세션에서 읽기 전용 사용자 계정 생성.
  READONLY_USER_PASSWORD="$(random_password)"
  http_get "${BASE_URL}/admin/users/new" "${ADMIN_JAR}"
  token="$(extract_csrf_token "${LAST_BODY_FILE}")"
  http_post_form "${BASE_URL}/admin/users" "${ADMIN_JAR}" "username=${READONLY_USER_NAME}" "password=${READONLY_USER_PASSWORD}" "role=readonly" "csrf_token=${token}"
  case "${LAST_STATUS}" in
    200|201|302)
      READONLY_USER_CREATED=1
      record pass admin_create_readonly_user POST "${BASE_URL}/admin/users" "${LAST_STATUS}" "${LAST_REDIRECT}" "created ${READONLY_USER_NAME}"
      ;;
    *)
      record blocked admin_create_readonly_user POST "${BASE_URL}/admin/users" "${LAST_STATUS}" "${LAST_REDIRECT}" "user creation route not available"
      ;;
  esac
fi

NORMAL_USER_AUTHENTICATED=0
if [ "${NORMAL_USER_CREATED}" -ne 1 ]; then
  record skip normal_user_login POST "${BASE_URL}/login" "n/a" "" "skipped: normal user account not created"
else
  # 8. 일반 사용자 세션으로 로그인.
  http_get "${BASE_URL}/login" "${USER_JAR}"
  token="$(extract_csrf_token "${LAST_BODY_FILE}")"
  http_post_form "${BASE_URL}/login" "${USER_JAR}" "username=${NORMAL_USER_NAME}" "password=${NORMAL_USER_PASSWORD}" "csrf_token=${token}"
  case "${LAST_STATUS}" in
    200|302)
      NORMAL_USER_AUTHENTICATED=1
      record pass normal_user_login POST "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "logged in as ${NORMAL_USER_NAME}"
      ;;
    *)
      record fail normal_user_login POST "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "login rejected for newly created normal user"
      ;;
  esac
fi

if [ "${NORMAL_USER_AUTHENTICATED}" -ne 1 ]; then
  record skip normal_user_document_write_check POST "${BASE_URL}/documents" "n/a" "" "skipped: normal user session not authenticated"
else
  # 9. 일반 사용자 세션에서 문서 생성/편집 허용 여부 확인.
  http_get "${BASE_URL}/documents/new" "${USER_JAR}"
  token="$(extract_csrf_token "${LAST_BODY_FILE}")"
  http_post_form "${BASE_URL}/documents" "${USER_JAR}" "title=${DOC_PREFIX}-by-user" "source=smoke test by normal user ${RUN_ID}" "csrf_token=${token}"
  case "${LAST_STATUS}" in
    200|201|302)
      record pass normal_user_document_write_check POST "${BASE_URL}/documents" "${LAST_STATUS}" "${LAST_REDIRECT}" "normal user allowed to create/edit documents"
      LEFTOVER_NOTES+=("document titled ${DOC_PREFIX}-by-user created by normal user — verify cleanup manually")
      ;;
    401|403)
      record fail normal_user_document_write_check POST "${BASE_URL}/documents" "${LAST_STATUS}" "${LAST_REDIRECT}" "normal user was denied document write, expected allowed"
      ;;
    *)
      record blocked normal_user_document_write_check POST "${BASE_URL}/documents" "${LAST_STATUS}" "${LAST_REDIRECT}" "document create route not available"
      ;;
  esac
fi

READONLY_USER_AUTHENTICATED=0
if [ "${READONLY_USER_CREATED}" -ne 1 ]; then
  record skip readonly_user_login POST "${BASE_URL}/login" "n/a" "" "skipped: readonly user account not created"
else
  # 10. 읽기 전용 사용자 세션으로 로그인.
  http_get "${BASE_URL}/login" "${READONLY_JAR}"
  token="$(extract_csrf_token "${LAST_BODY_FILE}")"
  http_post_form "${BASE_URL}/login" "${READONLY_JAR}" "username=${READONLY_USER_NAME}" "password=${READONLY_USER_PASSWORD}" "csrf_token=${token}"
  case "${LAST_STATUS}" in
    200|302)
      READONLY_USER_AUTHENTICATED=1
      record pass readonly_user_login POST "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "logged in as ${READONLY_USER_NAME}"
      ;;
    *)
      record fail readonly_user_login POST "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "login rejected for newly created readonly user"
      ;;
  esac
fi

if [ "${READONLY_USER_AUTHENTICATED}" -ne 1 ]; then
  record skip readonly_user_read_check GET "${BASE_URL}/" "n/a" "" "skipped: readonly user session not authenticated"
  record skip readonly_user_write_denied_check POST "${BASE_URL}/documents" "n/a" "" "skipped: readonly user session not authenticated"
else
  # 11. 읽기 전용 사용자 세션에서 문서 읽기 가능 여부 확인.
  http_get "${BASE_URL}/" "${READONLY_JAR}"
  case "${LAST_STATUS}" in
    2*) record pass readonly_user_read_check GET "${BASE_URL}/" "${LAST_STATUS}" "${LAST_REDIRECT}" "readonly user can read" ;;
    *) record fail readonly_user_read_check GET "${BASE_URL}/" "${LAST_STATUS}" "${LAST_REDIRECT}" "expected 2xx for read" ;;
  esac

  # 12. 읽기 전용 사용자 세션에서 문서 생성/편집이 거부되는지 확인.
  http_get "${BASE_URL}/documents/new" "${READONLY_JAR}"
  token="$(extract_csrf_token "${LAST_BODY_FILE}")"
  http_post_form "${BASE_URL}/documents" "${READONLY_JAR}" "title=${DOC_PREFIX}-by-readonly" "source=should be denied ${RUN_ID}" "csrf_token=${token}"
  case "${LAST_STATUS}" in
    401|403)
      record pass readonly_user_write_denied_check POST "${BASE_URL}/documents" "${LAST_STATUS}" "${LAST_REDIRECT}" "readonly user correctly denied write access"
      ;;
    200|201|302)
      record fail readonly_user_write_denied_check POST "${BASE_URL}/documents" "${LAST_STATUS}" "${LAST_REDIRECT}" "SECURITY: readonly user was allowed to write"
      LEFTOVER_NOTES+=("document titled ${DOC_PREFIX}-by-readonly may have been created by readonly user — verify and remove manually")
      ;;
    *)
      record blocked readonly_user_write_denied_check POST "${BASE_URL}/documents" "${LAST_STATUS}" "${LAST_REDIRECT}" "document create route not available, cannot confirm denial"
      ;;
  esac
fi

echo ""
echo "=== cleanup ==="
if [ "${KEEP_DATA}" -eq 1 ]; then
  echo "cleanup skipped (--keep-data)"
else
  if [ -n "${DOC_ID}" ] && [ "${DOC_DELETED}" -ne 1 ]; then
    echo "retry cleanup: document id=${DOC_ID}"
    retry_token="$(fresh_csrf_token "${BASE_URL}/documents/${DOC_ID}/edit" "${ADMIN_JAR}")"
    http_post_form "${BASE_URL}/documents/${DOC_ID}/delete" "${ADMIN_JAR}" "csrf_token=${retry_token}"
    case "${LAST_STATUS}" in
      200|204|302) echo "cleanup: document ${DOC_ID} deleted on retry" ;;
      *) LEFTOVER_NOTES+=("document id=${DOC_ID} title=${DOC_TITLE} still not cleaned up after retry (status=${LAST_STATUS})") ;;
    esac
  fi

  if [ "${NORMAL_USER_CREATED}" -eq 1 ]; then
    LEFTOVER_NOTES+=("account ${NORMAL_USER_NAME} has no delete-user route in this codebase yet — remove manually or via DB once available")
  fi
  if [ "${READONLY_USER_CREATED}" -eq 1 ]; then
    LEFTOVER_NOTES+=("account ${READONLY_USER_NAME} has no delete-user route in this codebase yet — remove manually or via DB once available")
  fi
  if [ "${ADMIN_LOGIN_USER}" = "${NEW_ADMIN_USER_NAME}" ]; then
    LEFTOVER_NOTES+=("account ${NEW_ADMIN_USER_NAME} was created by this run and has no delete-user route yet — remove manually or via DB once available")
  fi
fi

echo ""
echo "=== summary ==="
echo "pass=${PASS_COUNT} fail=${FAIL_COUNT} blocked=${BLOCKED_COUNT} skip=${SKIP_COUNT}"
if [ "${#LEFTOVER_NOTES[@]}" -gt 0 ]; then
  echo "leftover_data:"
  for note in "${LEFTOVER_NOTES[@]}"; do
    echo "  - ${note}"
  done
else
  echo "leftover_data: none"
fi

if [ "${APP_REACHABLE}" -ne 1 ]; then
  echo "live_e2e_smoke_test_status=blocked"
  exit 1
fi

if [ "${FAIL_COUNT}" -gt 0 ]; then
  echo "live_e2e_smoke_test_status=fail"
  exit 1
fi

echo "live_e2e_smoke_test_status=pass_or_blocked"
exit 0
