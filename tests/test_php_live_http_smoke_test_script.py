"""0671 실 배포 후 HTTP 스모크 테스트 스크립트
(`php/scripts/live-http-smoke-test.sh`)를 검증한다.

이 스크립트는 실제 curl 요청을 보내는 것이 목적이므로, 이 테스트는 네트워크
접속 없이도 통과해야 하는 CLI 계약(옵션 처리, 도움말, 오류 처리)만 확인한다.
실제 대상(`https://iowiki.iwinv.net/`)에 대한 실행 결과는
`docs/iowiki-shared-hosting-porting-log.md`에 기록되어 있다.
"""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "live-http-smoke-test.sh"
SCRIPTS_README_PATH = REPO_ROOT / "php" / "scripts" / "README.md"
PORTING_LOG_PATH = REPO_ROOT / "docs" / "iowiki-shared-hosting-porting-log.md"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_live_http_smoke_test_script_exists_and_is_executable():
    assert SCRIPT_PATH.is_file()
    assert os.access(SCRIPT_PATH, os.X_OK)


def test_live_http_smoke_test_script_has_valid_bash_syntax():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_live_http_smoke_test_script_supports_help():
    result = _run("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage: php/scripts/live-http-smoke-test.sh" in result.stdout
    assert "config/" in result.stdout
    assert "403" in result.stdout and "404" in result.stdout


def test_live_http_smoke_test_script_requires_base_url():
    result = _run()

    assert result.returncode == 2
    assert "Missing required option: --base-url" in result.stderr


def test_live_http_smoke_test_script_requires_base_url_value():
    result = _run("--base-url")

    assert result.returncode == 2
    assert "Missing value for --base-url" in result.stderr


def test_live_http_smoke_test_script_rejects_bad_options():
    result = _run("--nope")

    assert result.returncode == 2
    assert "Unknown live-http-smoke-test option: --nope" in result.stderr


def test_live_http_smoke_test_script_checks_all_sensitive_paths_from_security_checklist():
    """docs/shared-hosting-security-checklist.md가 다루는 공개 경로 노출 항목과
    동일한 경로 집합을 점검해야 한다."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    for path in ["config/", "vendor/", "storage/", "db/", "composer.json", "composer.lock", ".env"]:
        assert f'"{path}"' in content, f"missing sensitive path check: {path}"


def test_live_http_smoke_test_readme_documents_script():
    content = SCRIPTS_README_PATH.read_text(encoding="utf-8")

    assert "live-http-smoke-test.sh" in content


def test_porting_log_records_live_smoke_test_execution():
    """0671 acceptance criteria: iowiki.iwinv.net에서 HTTP 접속 smoke test를
    실제로 수행하고 그 결과를 기록해야 한다."""
    content = PORTING_LOG_PATH.read_text(encoding="utf-8")

    assert "live-http-smoke-test.sh" in content
    assert "https://iowiki.iwinv.net" in content
    assert "200" in content
