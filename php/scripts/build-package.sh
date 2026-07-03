#!/usr/bin/env bash
# PHP 공유 호스팅 배포 패키지 빌드 스크립트 골격.
# 실제 아카이브 생성 단계는 후속 태스크에서 추가하고, 여기서는 manifest와
# vendor 포함/미포함 모드를 명확히 분리해 후속 구현의 진입점을 고정한다.
set -euo pipefail

PHP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$PHP_ROOT/.." && pwd)"
MANIFEST_PATH="$PHP_ROOT/deployment-package-manifest.json"

usage() {
  cat <<'USAGE'
Usage: php/scripts/build-package.sh [--with-vendor|--without-vendor]

Modes:
  --without-vendor  Composer vendor 산출물을 제외한다. 기본값이다.
  --with-vendor     Composer vendor 산출물을 포함할 입력 목록을 선택한다.
USAGE
}

mode="${1:---without-vendor}"

case "$mode" in
  --with-vendor|with-vendor)
    vendor_mode="with_vendor"
    ;;
  --without-vendor|without-vendor)
    vendor_mode="without_vendor"
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    echo "Unknown package mode: $mode" >&2
    exit 2
    ;;
esac

if [ ! -f "$MANIFEST_PATH" ]; then
  echo "deployment package manifest not found: $MANIFEST_PATH" >&2
  exit 1
fi

python3 - "$MANIFEST_PATH" "$vendor_mode" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
vendor_mode = sys.argv[2]

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
optional_include = manifest.get("optional_include", {})

if vendor_mode not in optional_include:
    raise SystemExit(f"manifest optional_include에 {vendor_mode!r} 모드가 없습니다.")

package_name = manifest["package_name"]
base_path = manifest["base_path"]
include = manifest["include"]
mode_include = optional_include[vendor_mode]
exclude = manifest["exclude"]

print(f"package_name={package_name}")
print(f"base_path={base_path}")
print(f"vendor_mode={vendor_mode}")
print("include:")
for pattern in include:
    print(f"  {pattern}")
if mode_include:
    print("mode_include:")
    for pattern in mode_include:
        print(f"  {pattern}")
else:
    print("mode_include: none")
print("exclude:")
for pattern in exclude:
    print(f"  {pattern}")
PY

echo "Archive creation is intentionally not implemented in this skeleton."
echo "repo_root=$REPO_ROOT"
