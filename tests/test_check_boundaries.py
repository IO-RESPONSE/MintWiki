"""`scripts/check_boundaries.py` (도메인 이식성 경계 검사기) 의 동작을 검증한다.

이 스크립트는 지금까지 `scripts/qa.sh` 에 연결만 되어 있었을 뿐(태스크 0366
계열의 `tests/test_qa_script.py` 참고), 검사 로직 자체에 대한 단위 테스트가
없었다. 태스크 0379 는 그 공백을 메우고, 최상위 import 이름이 패키지명과
다른 프레임워크(예: ``pydantic-settings`` → ``pydantic_settings``)를 놓치던
탐지 공백을 보강한다.
"""
import importlib.util
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_boundaries.py"


def _load_script_module():
    """검사 대상 스크립트를 모듈로 로드한다 (scripts/ 는 패키지가 아니므로 직접 로드)."""
    spec = importlib.util.spec_from_file_location("check_boundaries", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def script():
    """`scripts/check_boundaries.py` 를 매번 새로 로드해 테스트 간 상태 오염을 막는다."""
    return _load_script_module()


class TestImportedRoots:
    """AST 에서 최상위 import 패키지명을 뽑아내는 imported_roots() 를 확인한다."""

    def test_collects_plain_import(self, script):
        tree = script.ast.parse("import fastapi\n")
        assert script.imported_roots(tree) == {"fastapi"}

    def test_collects_submodule_import_as_top_level_root(self, script):
        """``import a.b.c`` 는 최상위 ``a`` 로 환원되어야 한다."""
        tree = script.ast.parse("import sqlalchemy.ext.asyncio\n")
        assert script.imported_roots(tree) == {"sqlalchemy"}

    def test_collects_from_import_top_level_root(self, script):
        tree = script.ast.parse("from pydantic_settings import BaseSettings\n")
        assert script.imported_roots(tree) == {"pydantic_settings"}

    def test_ignores_relative_imports(self, script):
        """``from . import x`` 같은 상대 import(level>0) 는 무시해야 한다."""
        tree = script.ast.parse("from . import model\nfrom .. import service\n")
        assert script.imported_roots(tree) == set()

    def test_collects_multiple_aliases_on_one_line(self, script):
        tree = script.ast.parse("import os, fastapi as fa\n")
        assert script.imported_roots(tree) == {"os", "fastapi"}


class TestCheckFile:
    """단일 파일 위반 검사 함수 check_file() 을 확인한다."""

    def test_pure_domain_file_has_no_violations(self, tmp_path, script):
        path = tmp_path / "service.py"
        path.write_text("from typing import Optional\nimport uuid\n", encoding="utf-8")
        assert script.check_file(path) == []

    def test_generic_domain_file_rejects_forbidden_import(self, tmp_path, script):
        path = tmp_path / "service.py"
        path.write_text("import sqlalchemy\n", encoding="utf-8")
        violations = script.check_file(path)
        assert len(violations) == 1
        assert "sqlalchemy" in violations[0]

    def test_generic_domain_file_rejects_pydantic_settings(self, tmp_path, script):
        """pydantic-settings 는 import 루트가 'pydantic' 이 아니라 'pydantic_settings' 이므로
        FORBIDDEN_ROOTS 에 별도로 등록되어 있어야 잡힌다 (이번 보강의 핵심 대상)."""
        path = tmp_path / "service.py"
        path.write_text(
            "from pydantic_settings import BaseSettings\n", encoding="utf-8"
        )
        violations = script.check_file(path)
        assert len(violations) == 1
        assert "pydantic_settings" in violations[0]

    def test_router_py_allows_fastapi(self, tmp_path, script):
        path = tmp_path / "router.py"
        path.write_text("from fastapi import APIRouter\n", encoding="utf-8")
        assert script.check_file(path) == []

    def test_router_py_still_rejects_sqlalchemy(self, tmp_path, script):
        """router.py 예외는 fastapi/starlette 에만 적용되고, 다른 프레임워크는 여전히 막아야 한다."""
        path = tmp_path / "router.py"
        path.write_text("import sqlalchemy\n", encoding="utf-8")
        violations = script.check_file(path)
        assert len(violations) == 1
        assert "sqlalchemy" in violations[0]

    def test_repository_py_allows_sqlalchemy(self, tmp_path, script):
        path = tmp_path / "repository.py"
        path.write_text("import sqlalchemy\n", encoding="utf-8")
        assert script.check_file(path) == []

    def test_schema_py_allows_pydantic(self, tmp_path, script):
        path = tmp_path / "schema.py"
        path.write_text("import pydantic\n", encoding="utf-8")
        assert script.check_file(path) == []

    def test_schema_py_does_not_allow_pydantic_settings(self, tmp_path, script):
        """schema.py 의 예외는 순수 pydantic 만 허용하며, pydantic_settings 는 별개다."""
        path = tmp_path / "schema.py"
        path.write_text(
            "from pydantic_settings import BaseSettings\n", encoding="utf-8"
        )
        violations = script.check_file(path)
        assert len(violations) == 1
        assert "pydantic_settings" in violations[0]


class TestMainAgainstSyntheticDomain:
    """main() 을 합성 도메인 루트에 대해 실행해, 위반 보고와 종료 코드를 확인한다."""

    def test_reports_violation_and_exits_nonzero(self, tmp_path, monkeypatch, capsys):
        module = _load_script_module()
        (tmp_path / "service.py").write_text(
            textwrap.dedent(
                """
                from pydantic_settings import BaseSettings
                """
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(module, "DOMAIN_ROOT", tmp_path)
        exit_code = module.main()
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "pydantic_settings" in captured.err

    def test_passes_when_no_forbidden_imports(self, tmp_path, monkeypatch, capsys):
        module = _load_script_module()
        (tmp_path / "service.py").write_text("import uuid\n", encoding="utf-8")
        monkeypatch.setattr(module, "DOMAIN_ROOT", tmp_path)
        exit_code = module.main()
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "통과" in captured.out


class TestMainAgainstRealRepo:
    """실제 저장소의 도메인 계층(src/modules) 이 현재 경계를 통과하는지 회귀 고정한다."""

    def test_real_domain_layer_has_no_violations(self, monkeypatch):
        module = _load_script_module()
        monkeypatch.chdir(REPO_ROOT)
        assert module.main() == 0
