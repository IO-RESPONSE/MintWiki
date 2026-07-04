#!/usr/bin/env bash
# Plain FTP 전용 공유 호스팅에 배포 패키지를 업로드하는 스크립트.
#
# SSH/Composer/symlink 전환을 쓸 수 없는 계정(예: iowiki.iwinv.net)을 염두에
# 두고, docs/shared-hosting-provider-checklist-samples.md §3 (Plain FTP)의
# 업로드 순서를 lftp 배치 명령으로 옮긴 것이다. 자격증명은 환경변수
# (FTP_HOST/FTP_USER/FTP_PASSWORD) 또는 --password-file로만 받고, 비밀번호를
# 커맨드라인 인자나 로그로 남기지 않는다(비밀번호는 lftp 표준입력으로만 전달).
set -euo pipefail

REMOTE_ROOT="/"
DOCROOT_NAME="public_html"
BACKUP_DIR="./ftp-deploy-backups"
LOCAL_PUBLIC_DIR=""
PASSWORD_FILE=""
DRY_RUN=0
declare -a PRIVATE_MAPS=()

usage() {
  cat <<'USAGE'
Usage: php/scripts/ftp-deploy.sh --local-public-dir DIR [options]

Required:
  --local-public-dir DIR    docroot에 그대로 업로드할 로컬 디렉터리
                             (php/public/ 처럼 공개 파일만 포함해야 한다).

Options:
  --host HOST                FTP host (기본값: FTP_HOST 환경변수)
  --user USER                 FTP user (기본값: FTP_USER 환경변수)
  --password-file FILE        FTP 비밀번호만 담긴 파일 (기본값: FTP_PASSWORD 환경변수)
  --remote-root PATH           배포 전 이동할 FTP 루트 경로 (기본값: /)
  --docroot-name NAME          --remote-root 아래 공개 docroot 디렉터리명 (기본값: public_html)
  --private-map LOCAL:NAME     docroot 밖(형제 디렉터리)에 올릴 로컬 디렉터리:원격 이름 쌍.
                                여러 번 지정할 수 있다(config/src/vendor/storage/db 등).
  --backup-dir DIR              업로드 전 기존 원격 index.php 백업을 저장할 로컬 디렉터리
                                 (기본값: ./ftp-deploy-backups)
  --dry-run                     실제로 연결하지 않고 실행할 lftp 명령만 출력한다.
  -h, --help                    도움말을 출력한다.

이 스크립트는 FTP 비밀번호를 화면에 출력하거나 커맨드라인 인자로 받지 않는다.
--dry-run 에서는 비밀번호가 없어도 계획을 확인할 수 있다.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --local-public-dir)
      LOCAL_PUBLIC_DIR="${2:-}"
      shift 2
      ;;
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
    --private-map)
      PRIVATE_MAPS+=("${2:-}")
      shift 2
      ;;
    --backup-dir)
      BACKUP_DIR="${2:-}"
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
      echo "Unknown ftp-deploy option: $1" >&2
      exit 2
      ;;
  esac
done

if [ "${LOCAL_PUBLIC_DIR}" = "" ]; then
  usage >&2
  echo "Missing required option: --local-public-dir" >&2
  exit 2
fi

if [ ! -d "${LOCAL_PUBLIC_DIR}" ]; then
  echo "local public directory not found: ${LOCAL_PUBLIC_DIR}" >&2
  exit 1
fi

FTP_HOST="${FTP_HOST:-}"
FTP_USER="${FTP_USER:-}"

if [ "${FTP_HOST}" = "" ] || [ "${FTP_USER}" = "" ]; then
  echo "FTP_HOST and FTP_USER must be set (via --host/--user or env vars)." >&2
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

BACKUP_TIMESTAMP="$(date +%Y%m%d%H%M%S)"

build_lftp_script() {
  local password_placeholder="$1"
  cat <<LFTP
set ftp:ssl-allow no
open -u "${FTP_USER}","${password_placeholder}" "${FTP_HOST}"
cd "${REMOTE_ROOT}"
set cmd:fail-exit no
get "${DOCROOT_NAME}/index.php" -o "${BACKUP_DIR}/index.php.${BACKUP_TIMESTAMP}.bak"
set cmd:fail-exit yes
mirror --reverse --verbose "${LOCAL_PUBLIC_DIR}" "${DOCROOT_NAME}"
LFTP
  for map in "${PRIVATE_MAPS[@]:-}"; do
    [ -z "${map}" ] && continue
    local local_dir="${map%%:*}"
    local remote_name="${map#*:}"
    cat <<LFTP
mkdir -p "${remote_name}"
mirror --reverse --verbose "${local_dir}" "${remote_name}"
LFTP
  done
  echo "close"
}

if [ "${DRY_RUN}" -eq 1 ]; then
  echo "ftp_deploy_status=dry_run"
  echo "host=${FTP_HOST}"
  echo "user=${FTP_USER}"
  echo "remote_root=${REMOTE_ROOT}"
  echo "docroot_name=${DOCROOT_NAME}"
  echo "backup_dir=${BACKUP_DIR}"
  echo "--- lftp script (password redacted) ---"
  build_lftp_script "***REDACTED***"
  exit 0
fi

mkdir -p "${BACKUP_DIR}"
echo "index.php를 ${BACKUP_DIR}/index.php.${BACKUP_TIMESTAMP}.bak 로 백업한 뒤 배포를 시작합니다..."
build_lftp_script "${FTP_PASSWORD}" | lftp
echo "ftp_deploy_status=completed"
