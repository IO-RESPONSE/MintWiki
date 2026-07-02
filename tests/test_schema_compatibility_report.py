"""스키마 호환성 보고서 명령 테스트."""

import subprocess
import sys
from pathlib import Path


def test_schema_compatibility_report_script_exists():
    """스키마 호환성 보고서 스크립트가 존재하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )
    assert script_path.exists(), "schema_compatibility_report.py 스크립트가 없습니다"
    assert script_path.is_file(), "schema_compatibility_report.py이 파일이 아닙니다"


def test_schema_compatibility_report_script_is_executable():
    """스키마 호환성 보고서 스크립트가 실행 가능한지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )
    import os

    assert (
        os.access(script_path, os.X_OK)
    ), "schema_compatibility_report.py가 실행 가능하지 않습니다"


def test_schema_compatibility_report_imports():
    """호환성 보고서 스크립트가 필요한 의존성을 임포트할 수 있는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    # 스크립트를 파이썬으로 문법 확인
    with open(script_path, "r", encoding="utf-8") as f:
        try:
            compile(f.read(), str(script_path), "exec")
        except SyntaxError as e:
            raise AssertionError(
                f"schema_compatibility_report.py 문법 오류: {e}"
            ) from e


def test_schema_compatibility_report_execution():
    """호환성 보고서 스크립트가 정상 실행되는지 확인한다."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "scripts" / "schema_compatibility_report.py"

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
        f"호환성 보고서 실행이 실패했습니다 (종료 코드: {result.returncode})\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_schema_compatibility_report_has_checker_class():
    """호환성 보고서가 SchemaCompatibilityChecker 클래스를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "SchemaCompatibilityChecker" in content, (
            "호환성 보고서가 SchemaCompatibilityChecker 클래스를 포함하지 않습니다"
        )


def test_schema_compatibility_report_checks_column_types():
    """호환성 보고서가 컬럼 타입 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_column_types" in content, (
            "호환성 보고서가 컬럼 타입 검사 함수를 포함하지 않습니다"
        )


def test_schema_compatibility_report_checks_index_policies():
    """호환성 보고서가 인덱스 정책 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_index_policies" in content, (
            "호환성 보고서가 인덱스 정책 검사 함수를 포함하지 않습니다"
        )


def test_schema_compatibility_report_checks_transaction_patterns():
    """호환성 보고서가 트랜잭션 패턴 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_transaction_patterns" in content, (
            "호환성 보고서가 트랜잭션 패턴 검사 함수를 포함하지 않습니다"
        )


def test_schema_compatibility_report_checks_collation_settings():
    """호환성 보고서가 collation 설정 검사 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "check_collation_settings" in content, (
            "호환성 보고서가 collation 설정 검사 함수를 포함하지 않습니다"
        )


def test_schema_compatibility_report_generates_report():
    """호환성 보고서가 보고서 생성 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "generate_report" in content, (
            "호환성 보고서가 보고서 생성 함수를 포함하지 않습니다"
        )


def test_schema_compatibility_report_has_main_function():
    """호환성 보고서가 main 함수를 포함하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "def main()" in content, (
            "호환성 보고서가 main 함수를 포함하지 않습니다"
        )


def test_schema_compatibility_report_documents_postgresql_mariadb_differences():
    """호환성 보고서가 PostgreSQL/MariaDB 차이를 문서화하는지 확인한다.

    JSONB, ARRAY, ENUM 등 금지 항목과 TIMESTAMP, BOOLEAN 등 대체 필요 항목을 포함해야 한다.
    """
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        # 금지 항목 확인
        assert "JSONB" in content, "호환성 보고서가 JSONB 금지 항목을 문서화하지 않습니다"
        assert "ARRAY" in content, "호환성 보고서가 ARRAY 금지 항목을 문서화하지 않습니다"
        assert (
            "부분 인덱스" in content or "WHERE 절" in content
        ), "호환성 보고서가 부분 인덱스 금지 항목을 문서화하지 않습니다"


def test_schema_compatibility_report_tracks_issues_and_warnings():
    """호환성 보고서가 issues와 warnings를 추적하는지 확인한다."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "schema_compatibility_report.py"
    )

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "self.issues" in content, (
            "호환성 보고서가 issues 추적을 포함하지 않습니다"
        )
        assert "self.warnings" in content, (
            "호환성 보고서가 warnings 추적을 포함하지 않습니다"
        )
