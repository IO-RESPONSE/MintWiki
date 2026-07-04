"""PHP cutover 후 검증 명령 골격을 검증한다."""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATION_SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "post-cutover-validate.sh"
SCRIPTS_README_PATH = REPO_ROOT / "php" / "scripts" / "README.md"


def _run_validation_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(VALIDATION_SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_post_cutover_validation_script_exists_and_is_executable():
    """0667 cutover 후 검증 명령 골격이 실행 가능한 파일로 존재한다."""
    assert VALIDATION_SCRIPT_PATH.is_file()
    assert os.access(VALIDATION_SCRIPT_PATH, os.X_OK)


def test_post_cutover_validation_script_has_valid_bash_syntax():
    """후속 구현 전에도 bash 구문 오류가 없어야 한다."""
    result = subprocess.run(
        ["bash", "-n", str(VALIDATION_SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_post_cutover_validation_script_reports_required_checks():
    """health, DB, 문서 생성/조회 검증 계획을 모두 출력한다."""
    result = _run_validation_script("--base-url", "https://wiki.example.test/")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "post_cutover_validation_status=skeleton" in result.stdout
    assert "base_url=https://wiki.example.test" in result.stdout
    assert "health: GET https://wiki.example.test/health" in result.stdout
    assert "db: verify DB connection and schema readiness" in result.stdout
    assert "document_create: POST https://wiki.example.test/documents" in result.stdout
    assert (
        "document_view: GET https://wiki.example.test/documents/{created-document}"
        in result.stdout
    )
    assert "intentionally not implemented in this skeleton" in result.stdout


def test_post_cutover_validation_script_supports_help():
    """운영자가 cutover 후 검증 범위를 명령 도움말에서 확인할 수 있어야 한다."""
    result = _run_validation_script("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage: php/scripts/post-cutover-validate.sh" in result.stdout
    assert "health" in result.stdout
    assert "document_create" in result.stdout
    assert "does not send HTTP requests or write documents yet" in result.stdout


def test_post_cutover_validation_script_rejects_bad_options():
    """알 수 없는 옵션은 조용히 무시하지 않고 명확히 실패한다."""
    result = _run_validation_script("--check-now")

    assert result.returncode == 2
    assert "Unknown post-cutover validation option: --check-now" in result.stderr


def test_post_cutover_validation_script_requires_base_url_value():
    """--base-url 값 누락은 잘못된 실행으로 처리한다."""
    result = _run_validation_script("--base-url")

    assert result.returncode == 2
    assert "Missing value for --base-url" in result.stderr


def test_post_cutover_validation_readme_documents_script():
    """php/scripts 문서가 cutover 후 검증 스크립트를 안내한다."""
    content = SCRIPTS_README_PATH.read_text(encoding="utf-8")

    assert "post-cutover-validate.sh" in content
    assert "`--base-url`" in content
    assert "`/health`" in content
    assert "DB 연결/schema 준비 상태" in content
    assert "문서 생성" in content
