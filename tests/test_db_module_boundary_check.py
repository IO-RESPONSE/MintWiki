"""DB 모듈 경계 검사(0498)를 검증한다.

scripts/check_db_module_boundary.py가 DB 모듈(src/persistence/)과 도메인 계층
(src/modules/)의 경계를 정확히 검사하는지 확인한다.

규칙:
1. DB 모듈 내 특정 파일만 SQLAlchemy/asyncpg를 import할 수 있다
   (models.py, base.py, transaction.py, seed_loader.py, migration_state_service.py)
2. DbAdapter 인터페이스(db_adapter.py)는 SQLAlchemy를 import하지 않는다
3. 도메인 계층은 repository.py를 제외하고 SQLAlchemy를 직접 import하지 않는다
"""

import subprocess
import sys
from pathlib import Path


def _get_script_path() -> Path:
    """경계 검사 스크립트 경로를 반환한다."""
    return Path(__file__).parent.parent / "scripts" / "check_db_module_boundary.py"


def _run_boundary_check() -> tuple[int, str, str]:
    """경계 검사 스크립트를 실행하고 종료 코드, stdout, stderr을 반환한다."""
    script = _get_script_path()
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=str(script.parent.parent),
    )
    return result.returncode, result.stdout, result.stderr


def test_db_module_boundary_script_exists():
    """경계 검사 스크립트 파일이 존재하는지 확인한다."""
    script = _get_script_path()
    assert script.exists(), f"{script} should exist"


def test_db_module_boundary_script_is_executable():
    """경계 검사 스크립트가 실행 가능한지 확인한다."""
    import os

    script = _get_script_path()
    assert os.access(script, os.X_OK), f"{script} should be executable"


def test_db_module_boundary_check_passes_on_current_codebase():
    """현재 코드베이스가 DB 모듈 경계 검사를 통과하는지 확인한다."""
    returncode, stdout, stderr = _run_boundary_check()

    assert (
        returncode == 0
    ), f"Boundary check should pass. stderr: {stderr}\nstdout: {stdout}"
    assert "✅" in stdout or "✅" in stderr, "Success message should be present"


def test_db_module_boundary_check_validates_persistence_layer():
    """경계 검사가 src/persistence/ 계층을 검사하는지 확인한다."""
    returncode, stdout, stderr = _run_boundary_check()

    # 검사가 성공하면, DB 계층이 규칙을 따르고 있다는 뜻
    assert returncode == 0, "Current persistence layer should pass the check"


def test_db_module_boundary_check_validates_domain_layer():
    """경계 검사가 src/modules/ 계층을 검사하는지 확인한다."""
    returncode, stdout, stderr = _run_boundary_check()

    # 검사가 성공하면, 도메인이 규칙을 따르고 있다는 뜻
    assert returncode == 0, "Current domain layer should pass the check"


def test_db_adapter_interface_exists():
    """DbAdapter 인터페이스가 존재하고 SQL 라이브러리를 import하지 않는지 확인한다."""
    adapter_path = Path(__file__).parent.parent / "src" / "persistence" / "db_adapter.py"
    assert adapter_path.exists(), "src/persistence/db_adapter.py should exist"

    content = adapter_path.read_text()
    # DbAdapter는 순수 인터페이스이므로 SQLAlchemy를 import하면 안 됨
    assert "sqlalchemy" not in content, "DbAdapter should not import sqlalchemy"
    assert "asyncpg" not in content, "DbAdapter should not import asyncpg"
