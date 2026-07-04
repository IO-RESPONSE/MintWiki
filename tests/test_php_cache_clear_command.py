"""PHP 캐시 비우기 명령 골격을 검증한다."""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_CLEAR_SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "cache-clear.sh"
SCRIPTS_README_PATH = REPO_ROOT / "php" / "scripts" / "README.md"


def _run_cache_clear(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CACHE_CLEAR_SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_cache_clear_script_exists_and_is_executable():
    """0647 캐시 비우기 명령 골격이 실행 가능한 파일로 존재한다."""
    assert CACHE_CLEAR_SCRIPT_PATH.is_file()
    assert os.access(CACHE_CLEAR_SCRIPT_PATH, os.X_OK)


def test_cache_clear_script_has_valid_bash_syntax():
    """후속 구현 전에도 bash 구문 오류가 없어야 한다."""
    result = subprocess.run(
        ["bash", "-n", str(CACHE_CLEAR_SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_cache_clear_script_reports_skeleton_status():
    """현재 태스크는 삭제 로직 대신 명령 진입점만 고정한다."""
    result = _run_cache_clear()

    assert result.returncode == 0, result.stdout + result.stderr
    assert "cache_clear_status=skeleton" in result.stdout
    assert "php_root=" in result.stdout
    assert "not implemented in this skeleton" in result.stdout


def test_cache_clear_script_supports_help():
    """공유 호스팅 운영자가 명령 용도를 확인할 수 있어야 한다."""
    result = _run_cache_clear("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage: php/scripts/cache-clear.sh" in result.stdout
    assert "does not delete cache data yet" in result.stdout


def test_cache_clear_script_rejects_unknown_options():
    """알 수 없는 옵션은 조용히 무시하지 않고 명확히 실패한다."""
    result = _run_cache_clear("--all")

    assert result.returncode == 2
    assert "Unknown cache clear option: --all" in result.stderr


def test_cache_clear_readme_documents_shared_hosting_without_cli_fallback():
    """CLI가 없는 공유 호스팅 대안이 php/scripts 문서에 남아 있어야 한다."""
    content = SCRIPTS_README_PATH.read_text(encoding="utf-8")

    assert "cache-clear.sh" in content
    assert "공유 호스팅에서 CLI 실행 권한이 없으면" in content
    assert "호스팅 파일 관리자나 SFTP" in content
    assert "디렉터리 자체는 삭제하지 않는다" in content
