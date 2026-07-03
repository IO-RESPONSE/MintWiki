"""PHP 배포 패키지 빌드 스크립트 골격을 검증한다."""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "build-package.sh"


def _run_build_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(BUILD_SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_package_build_script_exists_and_is_executable():
    """0641 패키지 빌드 스크립트 골격이 실행 가능한 파일로 존재한다."""
    assert BUILD_SCRIPT_PATH.is_file()
    assert os.access(BUILD_SCRIPT_PATH, os.X_OK)


def test_package_build_script_has_valid_bash_syntax():
    """후속 구현 전에도 bash 구문 오류가 없어야 한다."""
    result = subprocess.run(
        ["bash", "-n", str(BUILD_SCRIPT_PATH)], capture_output=True, text=True
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_package_build_script_defaults_to_without_vendor_mode():
    """인자 없이 실행하면 vendor 미포함 모드를 선택한다."""
    result = _run_build_script()

    assert result.returncode == 0, result.stdout + result.stderr
    assert "vendor_mode=without_vendor" in result.stdout
    assert "mode_include: none" in result.stdout
    assert "php/vendor/**" in result.stdout


def test_package_build_script_supports_with_vendor_mode():
    """vendor 포함 모드는 manifest의 선택 입력 목록을 출력한다."""
    result = _run_build_script("--with-vendor")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "vendor_mode=with_vendor" in result.stdout
    assert "mode_include:" in result.stdout
    assert "  php/composer.lock" in result.stdout
    assert "  php/vendor/**" in result.stdout


def test_package_build_script_rejects_unknown_mode():
    """알 수 없는 모드는 명확히 실패해 잘못된 패키징을 막는다."""
    result = _run_build_script("--vendor")

    assert result.returncode == 2
    assert "Unknown package mode: --vendor" in result.stderr
    assert "--with-vendor" in result.stderr
    assert "--without-vendor" in result.stderr
