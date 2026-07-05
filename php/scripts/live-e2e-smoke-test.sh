#!/usr/bin/env bash
# 라이브 호스팅 배포본에 대한 API/HTTP 기반 end-to-end smoke test (태스크 0672,
# 실사용 흐름에 맞춘 0688 갱신).
#
# post-cutover-validate.sh(골격)나 live-http-smoke-test.sh(루트 응답/민감
# 경로 차단만 확인)와 달리, 이 스크립트는 관리자 세션으로 실제 로그인,
# 설치 마법사(`/install`) 접속 상태, 문서 생성/편집/조회, 익명 사용자에 대한
# 권한(읽기 허용/쓰기 거부) 확인을 curl로 직접 수행하고 결과를 기록한다.
#
# 0672 작성 시점에는 `php/public/index.php`가 `GET /`와 `GET /health`만
# 연결되어 있어 `/documents`, `/admin/users` 같은 가상의 route를 대상으로
# 했다. 0673-0687에서 실제로 연결된 route는 `/install*`, `/login`,
# `/logout`, `GET /wiki/{title}`, `GET`/`POST /wiki/{title}/edit`뿐이고
# (사용자 역할별 계정을 만드는 관리자 route는 아직 존재하지 않는다), 이
# 스크립트는 그 실제 route만 대상으로 한다. 각 시나리오는 실패해도
# 스크립트를 중단하지 않는다 — route가 없거나(404) 이전 단계가 실패하면
# "blocked"/"skip"으로 기록하고 다음 단계로 넘어간다.
set -uo pipefail

BASE_URL=""
KEEP_DATA=0

usage() {
  cat <<'USAGE'
Usage: php/scripts/live-e2e-smoke-test.sh --base-url URL [options]

라이브 배포본에 대해 아래 순서로 실제 HTTP 요청을 보내고 결과를 기록한다:
  1. GET /health 로 배포 상태를 확인한다(전제 조건).
  2. 익명 사용자로 공개 홈페이지 읽기를 확인한다.
  2.5. 스킨(Phase H, 0689-0694) 통합 확인: 홈 HTML의 상단바 마크업,
     design-tokens.css의 브랜드색(#008485), sidebar.css의 반응형
     @media 규칙이 실제로 배포되어 있는지 확인한다(자격 증명 불필요).
  3. GET /install 로 설치 마법사 접속 상태(설치 필요/이미 완료)를 확인한다.
  4. 기존 관리자 계정(SMOKE_ADMIN_USER/SMOKE_ADMIN_PASSWORD)으로 로그인한다.
  5. 관리자 세션으로 테스트 문서를 생성한다(GET/POST /wiki/{title}/edit).
  6. 생성한 문서를 조회한다(GET /wiki/{title}). 조회에 성공하면 문서
     액션 탭(document-tabs, 태스크 0692) 마크업도 함께 확인한다.
  7. 관리자 세션으로 테스트 문서를 편집한다(GET/POST /wiki/{title}/edit).
  8. 익명 사용자로 같은 문서를 읽을 수 있는지 확인한다(권한 확인: 읽기 허용).
  9. 익명 사용자가 같은 문서 편집을 시도하면 거부되는지 확인한다(권한 확인:
     쓰기 거부, `/login`으로 리다이렉트).

각 단계는 실패해도 스크립트를 중단하지 않는다 — route가 아직 연결되지
않았거나(404) 전제 단계가 실패하면 "blocked"/"skip"으로 기록하고 다음
단계로 넘어간다. SMOKE_ADMIN_USER/SMOKE_ADMIN_PASSWORD가 없으면 로그인이
필요한 모든 단계(5-9)를 안전하게 skip한다 — 설치 마법사를 거쳐 관리자
계정을 만드는 것은 실제 자격 증명을 가진 운영자가 브라우저로 수행할 일이며
(이 저장소의 `/install`은 DB 접속 정보·schema 적용·관리자 계정 생성을
여러 단계로 나눠 처리하는 실제 설치 절차다), 이 스크립트가 대신 만들지
않는다.

Options:
  --base-url URL           확인할 공개 URL (필수).
  --keep-data               정리(cleanup) 단계를 건너뛴다(디버깅용).
  -h, --help                 도움말을 출력한다.

환경변수(선택, 값은 출력/로그에 남기지 않는다):
  SMOKE_ADMIN_USER, SMOKE_ADMIN_PASSWORD   설치 마법사로 이미 만들어진
                                             관리자 계정. 비어 있으면
                                             로그인이 필요한 단계를 모두
                                             skip한다.

테스트 문서 제목은 SmokeTest-YYYYMMDD-HHMMSS 접두사를 사용한다.
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
DOC_TITLE="SmokeTest-${RUN_ID}"
ADMIN_USER_NAME="${SMOKE_ADMIN_USER:-}"
ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "${WORKDIR}"' EXIT

ADMIN_JAR="${WORKDIR}/admin-cookies.txt"
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

echo "base_url=${BASE_URL}"
echo "run_id=${RUN_ID}"
echo "doc_title=${DOC_TITLE}"
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

# 1. 익명 사용자 공개 페이지 읽기 확인 (홈페이지).
http_get "${BASE_URL}/" "${ANON_JAR}"
case "${LAST_STATUS}" in
  2*) record pass anonymous_read_home GET "${BASE_URL}/" "${LAST_STATUS}" "${LAST_REDIRECT}" "public home page readable" ;;
  *) record fail anonymous_read_home GET "${BASE_URL}/" "${LAST_STATUS}" "${LAST_REDIRECT}" "expected 2xx" ;;
esac

# 1.5 스킨(Phase H, 0689-0691) 통합 확인: 홈 HTML에 상단바 마크업이 있고,
#     design-tokens.css asset에 브랜드색(#008485) 토큰이 실제로 배포되어
#     있는지 확인한다. 자격 증명이 필요 없는 공개 확인이므로 /health
#     전제 조건에만 의존한다.
if [ "${APP_REACHABLE}" -ne 1 ]; then
  record blocked skin_top_bar_and_brand_check GET "${BASE_URL}/" "n/a" "" "skipped: /health precondition failed"
else
  if [ "${LAST_STATUS}" = "200" ] && grep -q 'class="site-nav"' "${LAST_BODY_FILE}" 2>/dev/null; then
    http_get "${BASE_URL}/assets/css/design-tokens.css" "${ANON_JAR}"
    case "${LAST_STATUS}" in
      200)
        if grep -q '#008485' "${LAST_BODY_FILE}" 2>/dev/null; then
          record pass skin_top_bar_and_brand_check GET "${BASE_URL}/assets/css/design-tokens.css" "${LAST_STATUS}" "${LAST_REDIRECT}" "home page has top bar markup and brand color #008485 is deployed"
        else
          record fail skin_top_bar_and_brand_check GET "${BASE_URL}/assets/css/design-tokens.css" "${LAST_STATUS}" "${LAST_REDIRECT}" "design-tokens.css missing #008485 brand color"
        fi
        ;;
      *) record fail skin_top_bar_and_brand_check GET "${BASE_URL}/assets/css/design-tokens.css" "${LAST_STATUS}" "${LAST_REDIRECT}" "expected 200 for design-tokens.css asset" ;;
    esac
  else
    record fail skin_top_bar_and_brand_check GET "${BASE_URL}/" "${LAST_STATUS}" "${LAST_REDIRECT}" "home page missing top nav bar (class=\"site-nav\") markup"
  fi
fi

# 1.6 스킨(태스크 0694) 통합 확인: sidebar.css asset이 좁은 화면을 위한
#     @media 반응형 규칙을 포함한 채로 배포되어 있는지 확인한다.
if [ "${APP_REACHABLE}" -ne 1 ]; then
  record blocked skin_responsive_asset_check GET "${BASE_URL}/assets/css/sidebar.css" "n/a" "" "skipped: /health precondition failed"
else
  http_get "${BASE_URL}/assets/css/sidebar.css" "${ANON_JAR}"
  case "${LAST_STATUS}" in
    200)
      if grep -q '@media (max-width:' "${LAST_BODY_FILE}" 2>/dev/null; then
        record pass skin_responsive_asset_check GET "${BASE_URL}/assets/css/sidebar.css" "${LAST_STATUS}" "${LAST_REDIRECT}" "sidebar.css has responsive @media rule"
      else
        record fail skin_responsive_asset_check GET "${BASE_URL}/assets/css/sidebar.css" "${LAST_STATUS}" "${LAST_REDIRECT}" "sidebar.css missing responsive @media rule"
      fi
      ;;
    *) record fail skin_responsive_asset_check GET "${BASE_URL}/assets/css/sidebar.css" "${LAST_STATUS}" "${LAST_REDIRECT}" "expected 200 for sidebar.css asset" ;;
  esac
fi

# 2. 설치 마법사(/install) 접속 상태 확인. 200이면 아직 설치 전, 403이면
#    이미 설치가 끝나 InstallerRouteGate가 차단한 것 — 둘 다 정상 상태이며,
#    이 스크립트는 실제 DB 자격 증명이 필요한 설치 절차 자체는 대신
#    수행하지 않는다(브라우저로 운영자가 수행, Notes 참고).
if [ "${APP_REACHABLE}" -ne 1 ]; then
  record blocked install_wizard_reachability GET "${BASE_URL}/install" "n/a" "" "skipped: /health precondition failed"
else
  http_get "${BASE_URL}/install" "${ANON_JAR}"
  case "${LAST_STATUS}" in
    200) record pass install_wizard_reachability GET "${BASE_URL}/install" "${LAST_STATUS}" "${LAST_REDIRECT}" "install wizard reachable (not yet installed)" ;;
    403) record pass install_wizard_reachability GET "${BASE_URL}/install" "${LAST_STATUS}" "${LAST_REDIRECT}" "install wizard blocked (already installed)" ;;
    *) record fail install_wizard_reachability GET "${BASE_URL}/install" "${LAST_STATUS}" "${LAST_REDIRECT}" "expected 200 (not installed) or 403 (already installed)" ;;
  esac
fi

# 3. 기존 관리자 계정으로 로그인. 자격 증명이 없으면 이후 관리자 세션이
#    필요한 모든 단계를 안전하게 skip한다.
ADMIN_AUTHENTICATED=0
if [ "${APP_REACHABLE}" -ne 1 ]; then
  record blocked admin_login GET/POST "${BASE_URL}/login" "n/a" "" "skipped: /health precondition failed"
elif [ -z "${ADMIN_USER_NAME}" ] || [ -z "${ADMIN_PASSWORD}" ]; then
  record skip admin_login GET/POST "${BASE_URL}/login" "n/a" "" "skipped: SMOKE_ADMIN_USER/SMOKE_ADMIN_PASSWORD not provided"
else
  http_get "${BASE_URL}/login" "${ADMIN_JAR}"
  if [ "${LAST_STATUS}" = "200" ]; then
    token="$(extract_csrf_token "${LAST_BODY_FILE}")"
    http_post_form "${BASE_URL}/login" "${ADMIN_JAR}" "username=${ADMIN_USER_NAME}" "password=${ADMIN_PASSWORD}" "csrf_token=${token}"
    case "${LAST_STATUS}" in
      200|302)
        ADMIN_AUTHENTICATED=1
        record pass admin_login POST "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "logged in as ${ADMIN_USER_NAME}"
        ;;
      *)
        record fail admin_login POST "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "login rejected for existing admin account"
        ;;
    esac
  else
    record blocked admin_login GET "${BASE_URL}/login" "${LAST_STATUS}" "${LAST_REDIRECT}" "login form route not available"
  fi
fi

# 4. 관리자 세션에서 테스트 문서 생성 (GET/POST /wiki/{title}/edit).
DOC_CREATED=0
if [ "${ADMIN_AUTHENTICATED}" -ne 1 ]; then
  record skip admin_create_document GET/POST "${BASE_URL}/wiki/${DOC_TITLE}/edit" "n/a" "" "skipped: no authenticated admin session"
else
  http_get "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${ADMIN_JAR}"
  if [ "${LAST_STATUS}" = "200" ]; then
    token="$(extract_csrf_token "${LAST_BODY_FILE}")"
    http_post_form "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${ADMIN_JAR}" "title=${DOC_TITLE}" "source=smoke test body ${RUN_ID}" "csrf_token=${token}"
    case "${LAST_STATUS}" in
      302)
        DOC_CREATED=1
        record pass admin_create_document POST "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "created document title=${DOC_TITLE}"
        ;;
      *)
        record fail admin_create_document POST "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "document create rejected"
        ;;
    esac
  else
    record blocked admin_create_document GET "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "document create form route not available"
  fi
fi

# 5. 생성한 문서 조회 확인 (GET /wiki/{title}).
if [ "${DOC_CREATED}" -ne 1 ]; then
  record skip admin_view_document GET "${BASE_URL}/wiki/${DOC_TITLE}" "n/a" "" "skipped: document was not created"
  record skip skin_document_action_tabs_check GET "${BASE_URL}/wiki/${DOC_TITLE}" "n/a" "" "skipped: no authenticated admin session/document"
else
  http_get "${BASE_URL}/wiki/${DOC_TITLE}" "${ADMIN_JAR}"
  case "${LAST_STATUS}" in
    200) record pass admin_view_document GET "${BASE_URL}/wiki/${DOC_TITLE}" "${LAST_STATUS}" "${LAST_REDIRECT}" "document viewable after create" ;;
    *) record fail admin_view_document GET "${BASE_URL}/wiki/${DOC_TITLE}" "${LAST_STATUS}" "${LAST_REDIRECT}" "expected 200" ;;
  esac

  # 5.1 스킨(태스크 0692) 통합 확인: 문서 view 응답에 문서 액션 탭
  #     (document-tabs) 마크업이 실제로 배포되어 있는지 확인한다.
  if [ "${LAST_STATUS}" = "200" ] && grep -q 'class="document-tabs"' "${LAST_BODY_FILE}" 2>/dev/null; then
    record pass skin_document_action_tabs_check GET "${BASE_URL}/wiki/${DOC_TITLE}" "${LAST_STATUS}" "${LAST_REDIRECT}" "document page has action tabs (document-tabs) markup"
  else
    record fail skin_document_action_tabs_check GET "${BASE_URL}/wiki/${DOC_TITLE}" "${LAST_STATUS}" "${LAST_REDIRECT}" "document page missing action tabs (class=\"document-tabs\") markup"
  fi
fi

# 6. 관리자 세션에서 테스트 문서 편집 (GET/POST /wiki/{title}/edit).
DOC_EDITED=0
if [ "${DOC_CREATED}" -ne 1 ]; then
  record skip admin_edit_document GET/POST "${BASE_URL}/wiki/${DOC_TITLE}/edit" "n/a" "" "skipped: document was not created"
else
  http_get "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${ADMIN_JAR}"
  if [ "${LAST_STATUS}" = "200" ]; then
    token="$(extract_csrf_token "${LAST_BODY_FILE}")"
    http_post_form "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${ADMIN_JAR}" "title=${DOC_TITLE}" "source=smoke test body edited ${RUN_ID}" "csrf_token=${token}"
    case "${LAST_STATUS}" in
      302)
        DOC_EDITED=1
        record pass admin_edit_document POST "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "edited document"
        ;;
      *)
        record fail admin_edit_document POST "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "document edit rejected"
        ;;
    esac
  else
    record blocked admin_edit_document GET "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "document edit form route not available"
  fi
fi

# 7. 권한 확인(읽기): 익명 사용자가 같은 문서를 읽을 수 있는지 확인한다
#    (DefaultPolicy: 공개 읽기 허용).
if [ "${DOC_CREATED}" -ne 1 ]; then
  record skip anonymous_read_document_check GET "${BASE_URL}/wiki/${DOC_TITLE}" "n/a" "" "skipped: document was not created"
else
  http_get "${BASE_URL}/wiki/${DOC_TITLE}" "${ANON_JAR}"
  case "${LAST_STATUS}" in
    200) record pass anonymous_read_document_check GET "${BASE_URL}/wiki/${DOC_TITLE}" "${LAST_STATUS}" "${LAST_REDIRECT}" "anonymous user can read document" ;;
    403) record fail anonymous_read_document_check GET "${BASE_URL}/wiki/${DOC_TITLE}" "${LAST_STATUS}" "${LAST_REDIRECT}" "anonymous user denied read, expected allowed by default policy" ;;
    *) record blocked anonymous_read_document_check GET "${BASE_URL}/wiki/${DOC_TITLE}" "${LAST_STATUS}" "${LAST_REDIRECT}" "unexpected status" ;;
  esac
fi

# 8. 권한 확인(쓰기 거부): 익명 사용자가 같은 문서 편집을 시도하면
#    거부되는지 확인한다 (DefaultPolicy: 익명 편집 거부, /login으로 redirect).
if [ "${DOC_CREATED}" -ne 1 ]; then
  record skip anonymous_edit_denied_check GET "${BASE_URL}/wiki/${DOC_TITLE}/edit" "n/a" "" "skipped: document was not created"
else
  http_get "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${ANON_JAR}"
  case "${LAST_STATUS}" in
    302)
      case "${LAST_REDIRECT}" in
        */login) record pass anonymous_edit_denied_check GET "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "anonymous user correctly redirected to login" ;;
        *) record fail anonymous_edit_denied_check GET "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "redirected somewhere other than /login" ;;
      esac
      ;;
    200) record fail anonymous_edit_denied_check GET "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "SECURITY: anonymous user was allowed to see the edit form" ;;
    *) record blocked anonymous_edit_denied_check GET "${BASE_URL}/wiki/${DOC_TITLE}/edit" "${LAST_STATUS}" "${LAST_REDIRECT}" "unexpected status" ;;
  esac
fi

echo ""
echo "=== cleanup ==="
if [ "${KEEP_DATA}" -eq 1 ]; then
  echo "cleanup skipped (--keep-data)"
elif [ "${DOC_CREATED}" -eq 1 ]; then
  LEFTOVER_NOTES+=("document title=${DOC_TITLE} has no delete route in this codebase yet — remove manually via DB once available")
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
