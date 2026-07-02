"""`scripts/check_contract_drift.py` 의 동작을 검증한다.

이 스크립트는 게이트가 아니라 정보성 리포트이므로, ``php/`` 트리가
없어도 항상 종료 코드 0 을 반환하고 모든 모듈을 ``not_measurable`` 로
보고하는지 확인한다. 태스크 0389 의 산출물이다.
"""
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_contract_drift.py"

VALID_MANIFEST = {
    "schema_version": "1.0",
    "module": "widget",
    "summary": "테스트용 위젯 모듈",
    "port": {"source_path": "src/modules/widget", "status": "not_started"},
    "service": {"path": "src/modules/widget/service.py", "public_methods": ["do_it"]},
    "repository": {
        "port_path": "src/modules/widget/repository.py",
        "interface": "WidgetRepository",
    },
    "fixtures": {"path": "tests/modules/widget/fixtures", "format": "json"},
}


def _load_script_module():
    """검사 대상 스크립트를 모듈로 로드한다 (scripts/ 는 패키지가 아니므로 직접 로드)."""
    spec = importlib.util.spec_from_file_location("check_contract_drift", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def script(tmp_path, monkeypatch):
    """모듈 루트를 임시 디렉토리로 바꿔치기한 스크립트 모듈을 반환한다."""
    module = _load_script_module()
    monkeypatch.setattr(module, "MODULES_ROOT", tmp_path)
    return module


class TestBuildReport:
    """build_report() 가 만드는 리포트 행을 검증한다."""

    def test_reports_not_measurable_when_php_root_missing(self, tmp_path, script):
        """php/ 트리가 없으면 모든 모듈의 drift 가 not_measurable 이다."""
        module_dir = tmp_path / "widget"
        module_dir.mkdir()
        (module_dir / "manifest.json").write_text(json.dumps(VALID_MANIFEST), encoding="utf-8")
        missing_php_root = tmp_path / "php"
        rows = script.build_report(php_root=missing_php_root)
        assert len(rows) == 1
        assert rows[0]["module"] == "widget"
        assert rows[0]["manifest_status"] == "not_started"
        assert rows[0]["php_tree_present"] is False
        assert rows[0]["drift"] == script.NOT_MEASURABLE

    def test_reports_unknown_status_when_manifest_missing(self, tmp_path, script):
        """manifest.json 이 없는 모듈은 manifest_status 가 unknown 이다."""
        module_dir = tmp_path / "orphan"
        module_dir.mkdir()
        rows = script.build_report(php_root=tmp_path / "php")
        assert rows[0]["module"] == "orphan"
        assert rows[0]["manifest_status"] == "unknown"

    def test_detects_php_root_presence(self, tmp_path, script):
        """php/ 트리가 존재하면 php_tree_present 가 True 다."""
        module_dir = tmp_path / "widget"
        module_dir.mkdir()
        (module_dir / "manifest.json").write_text(json.dumps(VALID_MANIFEST), encoding="utf-8")
        php_root = tmp_path / "php"
        php_root.mkdir()
        rows = script.build_report(php_root=php_root)
        assert rows[0]["php_tree_present"] is True
        # php/ 가 있어도 이 태스크 시점에는 실제 비교 로직이 없으므로
        # 여전히 not_measurable 로 보고한다.
        assert rows[0]["drift"] == script.NOT_MEASURABLE

    def test_excludes_pycache_directories(self, tmp_path, script):
        """__pycache__ 같은 비모듈 디렉토리는 리포트 대상에서 제외한다."""
        (tmp_path / "widget").mkdir()
        (tmp_path / "__pycache__").mkdir()
        rows = script.build_report(php_root=tmp_path / "php")
        assert {row["module"] for row in rows} == {"widget"}

    def test_rows_sorted_by_module_name(self, tmp_path, script):
        """리포트 행은 모듈 이름 순으로 정렬된다."""
        for name in ["zebra", "alpha", "mid"]:
            (tmp_path / name).mkdir()
        rows = script.build_report(php_root=tmp_path / "php")
        assert [row["module"] for row in rows] == ["alpha", "mid", "zebra"]


class TestFormatReport:
    """format_report() 가 사람이 읽을 수 있는 표를 만드는지 확인한다."""

    def test_includes_header_and_every_row(self, script):
        rows = [
            {
                "module": "widget",
                "manifest_status": "not_started",
                "php_tree_present": False,
                "drift": script.NOT_MEASURABLE,
            }
        ]
        text = script.format_report(rows)
        assert "module" in text
        assert "manifest_status" in text
        assert "widget" in text
        assert script.NOT_MEASURABLE in text


class TestMainAgainstRealRepo:
    """실제 저장소를 대상으로 스크립트 전체 실행을 검증한다."""

    def test_main_returns_zero_when_php_tree_absent(self, monkeypatch, capsys):
        """php/ 트리가 없어도 main() 은 실패(비정상 종료)하지 않는다."""
        module = _load_script_module()
        monkeypatch.chdir(REPO_ROOT)
        assert not module.PHP_ROOT.is_dir(), "이 태스크 시점에는 php/ 트리가 없어야 한다"
        exit_code = module.main()
        captured = capsys.readouterr()
        assert exit_code == 0
        assert "not_measurable" in captured.out
        assert "document" in captured.out

    def test_main_reports_every_real_module(self, monkeypatch, capsys):
        """실제 저장소의 모든 모듈이 리포트에 한 줄씩 나타난다."""
        module = _load_script_module()
        monkeypatch.chdir(REPO_ROOT)
        module.main()
        captured = capsys.readouterr()
        for module_dir in module.module_dirs():
            assert module_dir.name in captured.out
