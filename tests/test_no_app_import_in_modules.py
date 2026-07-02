"""`scripts/check_no_app_import_in_modules.py` (모듈 → app 역참조 검사기) 의 동작을 검증한다.

이 스크립트는 태스크 0380 의 산출물이다. ``src/app`` 은 FastAPI 부트스트랩(UI/API
어댑터) 계층이므로, ``src/modules`` 하위 도메인 코드가 이를 import(역참조)하면
안 된다. `scripts/check_boundaries.py` 가 프레임워크 누수를 막는 것과 별개로,
이 검사는 계층 간 의존 "방향"(app -> modules 만 허용) 자체를 강제한다.
"""
import importlib.util
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_no_app_import_in_modules.py"
QA_SCRIPT_PATH = REPO_ROOT / "scripts" / "qa.sh"


def _load_script_module():
    """검사 대상 스크립트를 모듈로 로드한다 (scripts/ 는 패키지가 아니므로 직접 로드)."""
    spec = importlib.util.spec_from_file_location(
        "check_no_app_import_in_modules", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def script():
    """`scripts/check_no_app_import_in_modules.py` 를 매번 새로 로드해 테스트 간 상태 오염을 막는다."""
    return _load_script_module()


class TestCheckFile:
    """단일 파일의 app 역참조 위반을 검사하는 check_file() 을 확인한다."""

    def test_pure_domain_file_has_no_violations(self, tmp_path, script):
        path = tmp_path / "service.py"
        path.write_text(
            "from modules.document.model import Document\n", encoding="utf-8"
        )
        assert script.check_file(path) == []

    def test_rejects_plain_app_import(self, tmp_path, script):
        path = tmp_path / "service.py"
        path.write_text("import app\n", encoding="utf-8")
        violations = script.check_file(path)
        assert len(violations) == 1
        assert "app" in violations[0]

    def test_rejects_from_app_submodule_import(self, tmp_path, script):
        path = tmp_path / "service.py"
        path.write_text("from app.config import Settings\n", encoding="utf-8")
        violations = script.check_file(path)
        assert len(violations) == 1
        assert "app" in violations[0]

    def test_does_not_false_positive_on_lookalike_package(self, tmp_path, script):
        """``application`` 처럼 'app' 로 시작하지만 다른 최상위 패키지는 오탐하지 않는다."""
        path = tmp_path / "service.py"
        path.write_text("import application_helpers\n", encoding="utf-8")
        assert script.check_file(path) == []

    def test_ignores_relative_imports(self, tmp_path, script):
        path = tmp_path / "service.py"
        path.write_text("from . import model\n", encoding="utf-8")
        assert script.check_file(path) == []


class TestMainAgainstSyntheticModules:
    """main() 을 합성 모듈 루트에 대해 실행해, 위반 보고와 종료 코드를 확인한다."""

    def test_reports_violation_and_exits_nonzero(self, tmp_path, monkeypatch, capsys):
        module = _load_script_module()
        (tmp_path / "service.py").write_text(
            textwrap.dedent(
                """
                from app.database import get_session
                """
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(module, "MODULES_ROOT", tmp_path)
        exit_code = module.main()
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "app" in captured.err

    def test_passes_when_no_app_imports(self, tmp_path, monkeypatch, capsys):
        module = _load_script_module()
        (tmp_path / "service.py").write_text("import uuid\n", encoding="utf-8")
        monkeypatch.setattr(module, "MODULES_ROOT", tmp_path)
        exit_code = module.main()
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "통과" in captured.out


class TestMainAgainstRealRepo:
    """실제 저장소의 src/modules 가 현재 app 역참조 금지 규칙을 통과하는지 회귀 고정한다."""

    def test_real_modules_have_no_app_imports(self, monkeypatch):
        module = _load_script_module()
        monkeypatch.chdir(REPO_ROOT)
        assert module.main() == 0


class TestQaScriptWiring:
    """qa.sh 가 이 검사를 boundary 검사와 test.sh 사이에서 실행하는지 확인한다."""

    def test_qa_runs_no_app_import_check(self):
        qa_contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
        assert "scripts/check_no_app_import_in_modules.py" in qa_contents

    def test_qa_runs_check_alongside_boundary_and_before_test(self):
        qa_contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
        boundary_index = qa_contents.index("scripts/check_boundaries.py")
        no_app_index = qa_contents.index("scripts/check_no_app_import_in_modules.py")
        test_index = qa_contents.index("scripts/test.sh")
        assert boundary_index < no_app_index < test_index
