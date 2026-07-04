"""0671 plain FTP 배포 스크립트(`php/scripts/ftp-deploy.sh`)를 검증한다."""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "ftp-deploy.sh"
SCRIPTS_README_PATH = REPO_ROOT / "php" / "scripts" / "README.md"


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    # 이전 세션에서 FTP_* 값이 새어 들어오지 않도록 매 실행마다 지운다.
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


def test_ftp_deploy_script_exists_and_is_executable():
    assert SCRIPT_PATH.is_file()
    assert os.access(SCRIPT_PATH, os.X_OK)


def test_ftp_deploy_script_has_valid_bash_syntax():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_ftp_deploy_script_supports_help():
    result = _run("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage: php/scripts/ftp-deploy.sh" in result.stdout
    assert "--local-public-dir" in result.stdout
    assert "--private-map" in result.stdout
    assert "비밀번호를 화면에 출력하거나 커맨드라인 인자로 받지 않는다" in result.stdout


def test_ftp_deploy_script_requires_local_public_dir():
    result = _run("--dry-run")

    assert result.returncode == 2
    assert "Missing required option: --local-public-dir" in result.stderr


def test_ftp_deploy_script_rejects_missing_local_dir(tmp_path):
    missing_dir = tmp_path / "does-not-exist"

    result = _run("--local-public-dir", str(missing_dir), "--dry-run")

    assert result.returncode == 1
    assert "local public directory not found" in result.stderr


def test_ftp_deploy_script_requires_host_and_user(tmp_path):
    local_dir = tmp_path / "public"
    local_dir.mkdir()

    result = _run("--local-public-dir", str(local_dir), "--dry-run")

    assert result.returncode == 2
    assert "FTP_HOST and FTP_USER must be set" in result.stderr


def test_ftp_deploy_script_dry_run_prints_plan_without_requiring_password(tmp_path):
    local_dir = tmp_path / "public"
    local_dir.mkdir()

    result = _run(
        "--local-public-dir", str(local_dir),
        "--private-map", f"{local_dir}:config",
        "--dry-run",
        env={"FTP_HOST": "iowiki.iwinv.net", "FTP_USER": "iowiki"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "ftp_deploy_status=dry_run" in result.stdout
    assert "host=iowiki.iwinv.net" in result.stdout
    assert 'open -u "iowiki","***REDACTED***" "iowiki.iwinv.net"' in result.stdout
    assert "mkdir -p \"config\"" in result.stdout
    assert 'get "public_html/index.php"' in result.stdout


def test_ftp_deploy_script_requires_password_when_not_dry_run(tmp_path):
    local_dir = tmp_path / "public"
    local_dir.mkdir()

    result = _run(
        "--local-public-dir", str(local_dir),
        env={"FTP_HOST": "iowiki.iwinv.net", "FTP_USER": "iowiki"},
    )

    assert result.returncode == 2
    assert "FTP password missing" in result.stderr


def test_ftp_deploy_script_rejects_bad_options():
    result = _run("--nope")

    assert result.returncode == 2
    assert "Unknown ftp-deploy option: --nope" in result.stderr


def test_ftp_deploy_script_never_accepts_bare_password_flag():
    """비밀번호를 커맨드라인 인자로 받는 옵션이 없어야 한다(ps 노출 방지)."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert '"--password")' not in content
    assert "--password-file" in content


def test_ftp_deploy_readme_documents_script():
    content = SCRIPTS_README_PATH.read_text(encoding="utf-8")

    assert "ftp-deploy.sh" in content
    assert "--private-map" in content
    assert "FTP_PASSWORD" in content
