"""PHP 앱 버전 파일을 검증한다."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_PATH = REPO_ROOT / "php" / "VERSION"
MANIFEST_PATH = REPO_ROOT / "php" / "deployment-package-manifest.json"


def test_php_version_file_exists():
    """PHP 패키지는 앱 버전을 별도 파일로 제공한다."""
    assert VERSION_PATH.is_file()


def test_php_version_file_uses_semver_text():
    """앱 버전은 schema version과 분리된 semver 텍스트이다."""
    version = VERSION_PATH.read_text(encoding="utf-8")

    assert version.endswith("\n")
    assert re.fullmatch(r"\d+\.\d+\.\d+\n", version)


def test_php_version_file_is_packaged_separately_from_manifest_schema_version():
    """배포 manifest는 VERSION 파일을 포함하고 app version 값을 중복 보관하지 않는다."""
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")

    assert '"php/VERSION"' in manifest_text
    assert '"app_version"' not in manifest_text
