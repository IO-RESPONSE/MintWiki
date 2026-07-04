"""0671 임시 phpinfo() 진단 스크립트(`php/scripts/phpinfo-probe.sh`)를 검증한다."""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "phpinfo-probe.sh"
SCRIPTS_README_PATH = REPO_ROOT / "php" / "scripts" / "README.md"


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    for key in ("FTP_HOST", "FTP_USER", "FTP_PASSWORD"):
        run_env.pop(key, None)
    if env:
        run_env.update(env)
    return subprocess.run(
        [str(SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=run_env,
    )


def test_phpinfo_probe_script_exists_and_is_executable():
    assert SCRIPT_PATH.is_file()
    assert os.access(SCRIPT_PATH, os.X_OK)


def test_phpinfo_probe_script_has_valid_bash_syntax():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_phpinfo_probe_script_supports_help():
    result = _run("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage: php/scripts/phpinfo-probe.sh" in result.stdout
    assert "--fetch" in result.stdout
    assert "항상 원격 진단 파일을 삭제" in result.stdout


def test_phpinfo_probe_script_requires_host_and_user():
    result = _run("--dry-run")

    assert result.returncode == 2
    assert "FTP_HOST and FTP_USER must be set" in result.stderr


def test_phpinfo_probe_script_fetch_requires_base_url():
    result = _run(
        "--fetch",
        "--dry-run",
        env={"FTP_HOST": "iowiki.iwinv.net", "FTP_USER": "iowiki"},
    )

    assert result.returncode == 2
    assert "--fetch requires --base-url" in result.stderr


def test_phpinfo_probe_script_dry_run_plans_upload_fetch_and_removal():
    result = _run(
        "--dry-run",
        "--fetch",
        "--base-url", "https://iowiki.iwinv.net",
        env={"FTP_HOST": "iowiki.iwinv.net", "FTP_USER": "iowiki"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "phpinfo_probe_status=dry_run" in result.stdout
    assert 'open -u "iowiki","***REDACTED***" "iowiki.iwinv.net"' in result.stdout
    assert "put " in result.stdout
    assert "curl -sS -o" in result.stdout
    assert 'rm "public_html/' in result.stdout


def test_phpinfo_probe_script_cleans_up_local_temp_file_on_dry_run(tmp_path):
    """dry-run이어도 로컬 임시 phpinfo 파일이 남지 않아야 한다."""
    result = _run(
        "--dry-run",
        env={"FTP_HOST": "iowiki.iwinv.net", "FTP_USER": "iowiki"},
        )

    assert result.returncode == 0, result.stdout + result.stderr
    # 스크립트가 생성한 mktemp 디렉터리 경로가 결과에 나타나므로, 그 경로가
    # 실행 종료 후에는 존재하지 않아야 한다.
    for line in result.stdout.splitlines():
        if line.startswith("put ") and " -o " in line:
            local_path = line.split('"')[1]
            assert not Path(local_path).exists()


def test_phpinfo_probe_script_rejects_bad_options():
    result = _run("--nope")

    assert result.returncode == 2
    assert "Unknown phpinfo-probe option: --nope" in result.stderr


def test_phpinfo_probe_readme_documents_script():
    content = SCRIPTS_README_PATH.read_text(encoding="utf-8")

    assert "phpinfo-probe.sh" in content
    assert "--fetch" in content
