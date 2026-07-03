"""UI 준비 상태 보고서 명령 테스트."""

import subprocess
import sys
from pathlib import Path


def test_ui_readiness_report_script_exists():
    """UI 준비 상태 보고서 스크립트가 존재하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )
    assert script_path.exists(), "ui_readiness_report.py 스크립트가 없습니다"
    assert script_path.is_file(), "ui_readiness_report.py이 파일이 아닙니다"


def test_ui_readiness_report_script_is_executable():
    """UI 준비 상태 보고서 스크립트가 실행 가능한지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )
    import os

    assert (
        os.access(script_path, os.X_OK)
    ), "ui_readiness_report.py가 실행 가능하지 않습니다"


def test_ui_readiness_report_imports():
    """UI 준비 상태 보고서 스크립트가 필요한 의존성을 임포트할 수 있는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    # 스크립트를 파이썬으로 문법 확인
    with open(script_path, "r", encoding="utf-8") as f:
        try:
            compile(f.read(), str(script_path), "exec")
        except SyntaxError as e:
            raise AssertionError(
                f"ui_readiness_report.py 문법 오류: {e}"
            ) from e


def test_ui_readiness_report_execution():
    """UI 준비 상태 보고서 스크립트가 정상 실행되는지 확인한다."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "scripts" / "ui_readiness_report.py"

    # 스크립트 실행
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )

    # 성공 종료 확인 (placeholder이므로 0 반환)
    assert result.returncode == 0, (
        f"UI 준비 상태 보고서 실행이 실패했습니다 (종료 코드: {result.returncode})\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_ui_readiness_report_has_reporter_class():
    """UI 준비 상태 보고서가 UIReadinessReporter 클래스를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "UIReadinessReporter" in content, (
            "UI 준비 상태 보고서가 UIReadinessReporter 클래스를 포함하지 않습니다"
        )


def test_ui_readiness_report_checks_router_completeness():
    """UI 준비 상태 보고서가 라우터 완성도 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_router_completeness" in content, (
            "UI 준비 상태 보고서가 라우터 완성도 검사 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_checks_html_escaping():
    """UI 준비 상태 보고서가 HTML Escaping 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_html_escaping" in content, (
            "UI 준비 상태 보고서가 HTML Escaping 검사 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_checks_csrf_defense():
    """UI 준비 상태 보고서가 CSRF 방어 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_csrf_defense" in content, (
            "UI 준비 상태 보고서가 CSRF 방어 검사 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_checks_security_headers():
    """UI 준비 상태 보고서가 보안 헤더 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_security_headers" in content, (
            "UI 준비 상태 보고서가 보안 헤더 검사 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_checks_mobile_responsiveness():
    """UI 준비 상태 보고서가 모바일 반응형 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_mobile_responsiveness" in content, (
            "UI 준비 상태 보고서가 모바일 반응형 검사 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_checks_accessibility_baseline():
    """UI 준비 상태 보고서가 접근성 기초 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_accessibility_baseline" in content, (
            "UI 준비 상태 보고서가 접근성 기초 검사 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_checks_static_assets():
    """UI 준비 상태 보고서가 정적 자산 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_static_assets" in content, (
            "UI 준비 상태 보고서가 정적 자산 검사 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_generates_report():
    """UI 준비 상태 보고서가 보고서 생성 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "generate_report" in content, (
            "UI 준비 상태 보고서가 보고서 생성 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_has_main_function():
    """UI 준비 상태 보고서가 main 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "def main()" in content, (
            "UI 준비 상태 보고서가 main 함수를 포함하지 않습니다"
        )


def test_ui_readiness_report_tracks_issues_and_warnings():
    """UI 준비 상태 보고서가 issues와 warnings를 추적하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "self.issues" in content, (
            "UI 준비 상태 보고서가 issues 추적을 포함하지 않습니다"
        )
        assert "self.warnings" in content, (
            "UI 준비 상태 보고서가 warnings 추적을 포함하지 않습니다"
        )


def test_ui_readiness_report_defines_phase_d_expectations():
    """UI 준비 상태 보고서가 Phase D 기대사항을 문서화하는지 확인한다.

    라우터, HTML escaping, CSRF, 보안 헤더, 모바일, 접근성, 정적 자산 등 7개 검사 항목을
    포함해야 한다.
    """
    script_path = (
        Path(__file__).parent.parent / "scripts" / "ui_readiness_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        # 7개 항목 확인
        assert "라우터" in content or "router" in content, (
            "UI 준비 상태 보고서가 라우터 항목을 문서화하지 않습니다"
        )
        assert "escaping" in content or "escaping" in content.lower(), (
            "UI 준비 상태 보고서가 HTML escaping 항목을 문서화하지 않습니다"
        )
        assert "CSRF" in content or "csrf" in content.lower(), (
            "UI 준비 상태 보고서가 CSRF 항목을 문서화하지 않습니다"
        )
        assert "헤더" in content or "header" in content.lower(), (
            "UI 준비 상태 보고서가 보안 헤더 항목을 문서화하지 않습니다"
        )
