"""0672 라이브 호스팅 API/HTTP E2E smoke test 스크립트
(`php/scripts/live-e2e-smoke-test.sh`)와 그 실행 기록 문서
(`docs/live-hosting-e2e-smoke-log.md`)를 검증한다.

이 스크립트는 실제 curl 요청을 라이브 URL로 보내는 것이 목적이므로,
이 테스트는 네트워크 접속 없이도 통과해야 하는 CLI 계약(옵션 처리,
도움말, 오류 처리, 시나리오 커버리지)만 확인한다. 실제 대상
(`https://iowiki.iwinv.net/`)에 대한 실행 결과는
`docs/live-hosting-e2e-smoke-log.md`에 기록되어 있다.

0688에서 시나리오 이름과 대상 route를 갱신했다: 0672 작성 시점에는
`php/public/index.php`가 `GET /`/`GET /health`만 연결되어 있어
`/documents`, `/admin/users` 같은 가상의 route를 대상으로 했지만,
0673-0687에서 실제로 연결된 route는 `/install*`, `/login`, `/logout`,
`/wiki/{title}`, `/wiki/{title}/edit`뿐이다(사용자 역할별 계정을 만드는
관리자 route는 아직 없다). 이 테스트는 그 실제 route를 대상으로 하는
새 시나리오 이름을 검증한다.
"""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "live-e2e-smoke-test.sh"
SCRIPTS_README_PATH = REPO_ROOT / "php" / "scripts" / "README.md"
REPORT_DOC_PATH = REPO_ROOT / "docs" / "live-hosting-e2e-smoke-log.md"


def _run(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        [str(SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_live_e2e_smoke_test_script_exists_and_is_executable():
    assert SCRIPT_PATH.is_file()
    assert os.access(SCRIPT_PATH, os.X_OK)


def test_live_e2e_smoke_test_script_has_valid_bash_syntax():
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_live_e2e_smoke_test_script_supports_help():
    result = _run("--help")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Usage: php/scripts/live-e2e-smoke-test.sh" in result.stdout
    assert "SMOKE_ADMIN_USER" in result.stdout
    assert "SMOKE_ADMIN_PASSWORD" in result.stdout


def test_live_e2e_smoke_test_script_requires_base_url():
    result = _run()

    assert result.returncode == 2
    assert "Missing required option: --base-url" in result.stderr


def test_live_e2e_smoke_test_script_requires_base_url_value():
    result = _run("--base-url")

    assert result.returncode == 2
    assert "Missing value for --base-url" in result.stderr


def test_live_e2e_smoke_test_script_rejects_bad_options():
    result = _run("--nope")

    assert result.returncode == 2
    assert "Unknown live-e2e-smoke-test option: --nope" in result.stderr


def test_live_e2e_smoke_test_script_never_puts_password_literal_in_argv_helpers():
    """비밀번호를 curl 커맨드라인 인자로 직접 넘기지 않고 config(stdin)로만
    전달해야 한다(ps 노출 방지)."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "-K " in content or "-K\"" in content
    assert "data-urlencode" in content


def test_live_e2e_smoke_test_script_covers_all_acceptance_scenarios():
    """0688 acceptance criteria(설치 마법사 -> 로그인 -> 문서 생성/편집/조회
    -> 권한 확인)가 요구하는, 실제로 연결된 route를 대상으로 하는 시나리오
    이름이 모두 스크립트에 있어야 한다."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    required_scenarios = [
        "health_check",
        "anonymous_read_home",
        "skin_top_bar_and_brand_check",
        "skin_responsive_asset_check",
        "anonymous_admin_denied_check",
        "install_wizard_reachability",
        "admin_login",
        "admin_console_routes_check",
        "admin_create_document",
        "admin_view_document",
        "skin_document_action_tabs_check",
        "admin_edit_document",
        "anonymous_read_document_check",
        "anonymous_edit_denied_check",
    ]
    for scenario in required_scenarios:
        assert scenario in content, f"missing scenario: {scenario}"


def test_live_e2e_smoke_test_script_checks_skin_markup_and_brand_color():
    """0695 acceptance criteria: 홈 HTML에 상단바 마크업과
    --color-brand/#008485 참조가 실제로 배포되어 있는지 확인해야 한다."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'class="site-nav"' in content
    assert "#008485" in content
    assert "design-tokens.css" in content
    assert "document-tabs" in content
    assert "@media (max-width:" in content


def test_live_e2e_smoke_test_script_skin_checks_skip_safely_without_precondition():
    """스킨 확인도 다른 시나리오와 동일하게 /health 전제 조건이나 관리자
    세션이 없으면 fail이 아니라 blocked/skip으로 안전하게 끝나야 한다."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'record blocked skin_top_bar_and_brand_check' in content
    assert 'record blocked skin_responsive_asset_check' in content
    assert 'record skip skin_document_action_tabs_check' in content


def test_live_e2e_smoke_test_script_targets_actually_wired_routes():
    """0672 작성 당시 가상의 route(`/documents`, `/admin/users`)가 아니라,
    0673-0687에서 실제로 연결된 route만 대상으로 해야 한다."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "/wiki/${DOC_TITLE}/edit" in content
    assert "/wiki/${DOC_TITLE}" in content
    assert "/install" in content
    assert "${BASE_URL}/documents" not in content
    assert "${BASE_URL}/admin/users" not in content


def test_live_e2e_smoke_test_script_skips_safely_without_admin_credentials():
    """SMOKE_ADMIN_USER/SMOKE_ADMIN_PASSWORD가 없으면 러너에서 실패하지
    않고 안전하게 skip해야 한다."""
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "SMOKE_ADMIN_USER/SMOKE_ADMIN_PASSWORD not provided" in content


def test_live_e2e_smoke_test_script_uses_required_naming_prefixes():
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "SmokeTest-" in content


def test_live_e2e_smoke_test_readme_documents_script():
    content = SCRIPTS_README_PATH.read_text(encoding="utf-8")

    assert "live-e2e-smoke-test.sh" in content


def test_live_hosting_e2e_smoke_log_records_execution():
    """0672 acceptance criteria: 라이브 사이트 base URL을 대상으로 실행한
    결과(HTTP status, 차단/스킵 사유, leftover 데이터 여부)를 기록해야 한다.
    """
    assert REPORT_DOC_PATH.is_file()
    content = REPORT_DOC_PATH.read_text(encoding="utf-8")

    assert "live-e2e-smoke-test.sh" in content
    assert "https://iowiki.iwinv.net" in content
    assert "leftover_data" in content


def test_live_hosting_e2e_smoke_log_never_contains_a_real_secret_looking_value():
    content = REPORT_DOC_PATH.read_text(encoding="utf-8").lower()
    for forbidden in ["password:", "password=", "smoke_admin_password=", "pwd:"]:
        assert forbidden not in content, f"possible credential leak: {forbidden}"
