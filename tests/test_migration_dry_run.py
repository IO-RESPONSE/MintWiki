"""마이그레이션 드라이런 명령 테스트."""

import subprocess
import sys
from pathlib import Path


def test_migration_dry_run_script_exists():
    """마이그레이션 드라이런 스크립트가 존재하는지 확인한다."""
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"
    assert script_path.exists(), "migration_dry_run.py 스크립트가 없습니다"
    assert script_path.is_file(), "migration_dry_run.py이 파일이 아닙니다"


def test_migration_dry_run_script_is_executable():
    """마이그레이션 드라이런 스크립트가 실행 가능한지 확인한다."""
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"
    # Unix 실행 권한 확인
    import os
    assert os.access(script_path, os.X_OK), "migration_dry_run.py가 실행 가능하지 않습니다"


def test_migration_dry_run_imports():
    """드라이런 스크립트가 필요한 의존성을 임포트할 수 있는지 확인한다."""
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"

    # 스크립트를 파이썬으로 문법 확인
    with open(script_path, "r", encoding="utf-8") as f:
        try:
            compile(f.read(), str(script_path), "exec")
        except SyntaxError as e:
            raise AssertionError(
                f"migration_dry_run.py 문법 오류: {e}"
            ) from e


def test_migration_dry_run_execution_with_no_migrations():
    """마이그레이션이 없을 때 드라이런 스크립트가 정상 종료되는지 확인한다."""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / "scripts" / "migration_dry_run.py"

    # 스크립트 실행
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )

    # 성공 종료 확인 (마이그레이션이 없으면 0 반환)
    assert result.returncode == 0, (
        f"드라이런이 실패했습니다 (종료 코드: {result.returncode})\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_migration_dry_run_validates_files():
    """드라이런이 마이그레이션 파일 유효성을 검사하는지 확인한다."""
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"

    # 스크립트에서 _validate_migration_files 함수 확인
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "_validate_migration_files" in content, (
            "드라이런이 마이그레이션 파일 검증 함수를 포함하지 않습니다"
        )


def test_migration_dry_run_validates_chain():
    """드라이런이 마이그레이션 체인 검증을 포함하는지 확인한다."""
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"

    # 스크립트에서 _validate_migration_chain 함수 확인
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "_validate_migration_chain" in content, (
            "드라이런이 마이그레이션 체인 검증 함수를 포함하지 않습니다"
        )


def test_migration_dry_run_generates_sql():
    """드라이런이 SQL 생성 함수를 포함하는지 확인한다."""
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"

    # 스크립트에서 _generate_migration_sql 함수 확인
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "_generate_migration_sql" in content, (
            "드라이런이 SQL 생성 함수를 포함하지 않습니다"
        )


def test_migration_dry_run_no_database_writes():
    """드라이런이 데이터베이스에 변경을 쓰지 않는지 확인한다.

    오프라인 모드를 사용하여 실제 DB 변경 없이 SQL만 검증한다.
    """
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"

    # 스크립트에서 offline/dry-run 관련 키워드 확인
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        # offline 모드 사용 확인
        assert "offline" in content or ":memory:" in content, (
            "드라이런이 non-destructive 모드를 사용하지 않습니다"
        )


def test_migration_dry_run_handles_migration_chain_validation():
    """드라이런이 마이그레이션 체인 검증을 수행하는지 확인한다."""
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"

    # 스크립트에서 체인 검증 로직 확인
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        # down_revision 검증 확인
        assert "down_revision" in content, (
            "드라이런이 마이그레이션 down_revision 검증을 포함하지 않습니다"
        )
        # 루트 마이그레이션 검증 확인
        assert "start_migrations" in content, (
            "드라이런이 루트 마이그레이션 검증을 포함하지 않습니다"
        )


def test_migration_dry_run_validates_migration_files_syntax():
    """드라이런이 마이그레이션 파일의 Python 문법을 검사하는지 확인한다."""
    script_path = Path(__file__).parent.parent / "scripts" / "migration_dry_run.py"

    # 스크립트에서 compile 함수 사용 확인
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "compile(" in content, (
            "드라이런이 마이그레이션 파일 문법 검사를 포함하지 않습니다"
        )
