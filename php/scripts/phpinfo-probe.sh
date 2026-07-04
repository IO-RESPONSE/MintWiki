#!/usr/bin/env bash
# FTP-only 공유 호스팅에서 PHP 버전/확장/loaded config/document root/rewrite
# 환경을 확인하기 위한 임시 phpinfo() 진단 파일을 올리고, 확인 후 반드시
# 원격/로컬 사본을 모두 삭제하는 스크립트.
#
# phpinfo()는 서버 경로, 환경변수, 설치된 모듈 등 민감한 정보를 포함할 수
# 있으므로 공개 URL에 오래 남기지 않는다(0671 Notes). 이 스크립트는 업로드,
# (선택) fetch, 삭제를 한 번의 실행으로 묶어 진단 파일이 남는 실수를 줄인다.
set -euo pipefail

REMOTE_ROOT="/"
DOCROOT_NAME="public_html"
FILE_PREFIX="phpinfo-probe"
PASSWORD_FILE=""
DRY_RUN=0
FETCH=0
BASE_URL=""
OUTPUT_FILE=""

usage() {
  cat <<'USAGE'
Usage: php/scripts/phpinfo-probe.sh [options]

Options:
  --host HOST              FTP host (기본값: FTP_HOST 환경변수)
  --user USER               FTP user (기본값: FTP_USER 환경변수)
  --password-file FILE      FTP 비밀번호만 담긴 파일 (기본값: FTP_PASSWORD 환경변수)
  --remote-root PATH         FTP 루트 경로 (기본값: /)
  --docroot-name NAME         업로드할 공개 docroot 디렉터리명 (기본값: public_html)
  --file-prefix PREFIX         임시 진단 파일 이름 접두어 (기본값: phpinfo-probe)
  --fetch --base-url URL        업로드 직후 해당 URL로 curl 요청해 결과를 저장한다.
  --output-file FILE            --fetch 결과를 저장할 로컬 파일 (기본값: ./<prefix>-output.html)
  --dry-run                     실제로 연결하지 않고 계획만 출력한다.
  -h, --help                    도움말을 출력한다.

이 스크립트는 성공/실패와 무관하게 항상 원격 진단 파일을 삭제하고 로컬 임시
파일도 정리한다(trap 기반 cleanup). FTP 비밀번호는 커맨드라인 인자로 받지 않는다.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host)
      FTP_HOST="${2:-}"
      shift 2
      ;;
    --user)
      FTP_USER="${2:-}"
      shift 2
      ;;
    --password-file)
      PASSWORD_FILE="${2:-}"
      shift 2
      ;;
    --remote-root)
      REMOTE_ROOT="${2:-}"
      shift 2
      ;;
    --docroot-name)
      DOCROOT_NAME="${2:-}"
      shift 2
      ;;
    --file-prefix)
      FILE_PREFIX="${2:-}"
      shift 2
      ;;
    --fetch)
      FETCH=1
      shift
      ;;
    --base-url)
      BASE_URL="${2%/}"
      shift 2
      ;;
    --output-file)
      OUTPUT_FILE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      echo "Unknown phpinfo-probe option: $1" >&2
      exit 2
      ;;
  esac
done

FTP_HOST="${FTP_HOST:-}"
FTP_USER="${FTP_USER:-}"

if [ "${FTP_HOST}" = "" ] || [ "${FTP_USER}" = "" ]; then
  echo "FTP_HOST and FTP_USER must be set (via --host/--user or env vars)." >&2
  exit 2
fi

if [ "${FETCH}" -eq 1 ] && [ "${BASE_URL}" = "" ]; then
  echo "--fetch requires --base-url." >&2
  exit 2
fi

if [ "${PASSWORD_FILE}" != "" ]; then
  if [ ! -f "${PASSWORD_FILE}" ]; then
    echo "password file not found: ${PASSWORD_FILE}" >&2
    exit 1
  fi
  FTP_PASSWORD="$(head -n 1 "${PASSWORD_FILE}")"
else
  FTP_PASSWORD="${FTP_PASSWORD:-}"
fi

if [ "${DRY_RUN}" -eq 0 ] && [ "${FTP_PASSWORD}" = "" ]; then
  echo "FTP password missing — set FTP_PASSWORD or pass --password-file (or use --dry-run)." >&2
  exit 2
fi

REMOTE_FILE_NAME="${FILE_PREFIX}_$(date +%Y%m%d%H%M%S)_${RANDOM}.php"
LOCAL_TMP_DIR="$(mktemp -d)"
LOCAL_TMP_FILE="${LOCAL_TMP_DIR}/${REMOTE_FILE_NAME}"
OUTPUT_FILE="${OUTPUT_FILE:-./${FILE_PREFIX}-output.html}"

cat > "${LOCAL_TMP_FILE}" <<'PHP'
<?php
// 임시 진단 파일 — phpinfo-probe.sh 가 업로드/삭제를 함께 관리한다.
phpinfo();
PHP

cleanup() {
  rm -f "${LOCAL_TMP_FILE}"
  rmdir "${LOCAL_TMP_DIR}" 2>/dev/null || true
}
trap cleanup EXIT

if [ "${DRY_RUN}" -eq 1 ]; then
  echo "phpinfo_probe_status=dry_run"
  echo "remote_file=${REMOTE_ROOT%/}/${DOCROOT_NAME}/${REMOTE_FILE_NAME}"
  echo "--- lftp script (password redacted) ---"
  cat <<LFTP
set ftp:ssl-allow no
open -u "${FTP_USER}","***REDACTED***" "${FTP_HOST}"
cd "${REMOTE_ROOT}"
put "${LOCAL_TMP_FILE}" -o "${DOCROOT_NAME}/${REMOTE_FILE_NAME}"
LFTP
  if [ "${FETCH}" -eq 1 ]; then
    echo "curl -sS -o \"${OUTPUT_FILE}\" \"${BASE_URL}/${REMOTE_FILE_NAME}\""
  fi
  cat <<LFTP
rm "${DOCROOT_NAME}/${REMOTE_FILE_NAME}"
close
LFTP
  exit 0
fi

lftp <<LFTP
set ftp:ssl-allow no
open -u "${FTP_USER}","${FTP_PASSWORD}" "${FTP_HOST}"
cd "${REMOTE_ROOT}"
put "${LOCAL_TMP_FILE}" -o "${DOCROOT_NAME}/${REMOTE_FILE_NAME}"
close
LFTP

remove_remote_probe() {
  lftp <<LFTP || true
set ftp:ssl-allow no
open -u "${FTP_USER}","${FTP_PASSWORD}" "${FTP_HOST}"
cd "${REMOTE_ROOT}"
rm "${DOCROOT_NAME}/${REMOTE_FILE_NAME}"
close
LFTP
}
trap 'remove_remote_probe; cleanup' EXIT

if [ "${FETCH}" -eq 1 ]; then
  curl -sS -o "${OUTPUT_FILE}" "${BASE_URL}/${REMOTE_FILE_NAME}" || true
  echo "phpinfo_probe_output=${OUTPUT_FILE}"
else
  echo "phpinfo_probe_url=${BASE_URL:-<base-url 미지정>}/${REMOTE_FILE_NAME}"
fi

echo "phpinfo_probe_status=uploaded_and_scheduled_for_removal"
echo "reminder: 위 remove 명령이 성공했는지 반드시 원격에서 재확인한다."
