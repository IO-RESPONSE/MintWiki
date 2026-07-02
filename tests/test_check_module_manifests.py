"""`scripts/check_module_manifests.py` 의 동작을 검증한다.

manifest 필수 필드 검증(스키마 위반)뿐 아니라, manifest.json 자체가 없는
모듈도 위반으로 잡아내는지 확인한다. 태스크 0365 의 산출물이다. QA 파이프
라인(scripts/qa.sh) 연결 여부는 tests/test_qa_script.py(태스크 0366)가
검증하므로 여기서는 스크립트 단독 동작만 검증한다.
"""
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_module_manifests.py"
REAL_SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"


def _load_script_module():
    """검사 대상 스크립트를 모듈로 로드한다 (scripts/ 는 패키지가 아니므로 직접 로드)."""
    spec = importlib.util.spec_from_file_location("check_module_manifests", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


@pytest.fixture()
def script(tmp_path, monkeypatch):
    """모듈 루트를 임시 디렉토리로 바꿔치기한 스크립트 모듈을 반환한다.

    실제 스키마 파일은 그대로 사용해, 스키마 자체가 아니라 스크립트 동작만
    격리해서 검증한다.
    """
    module = _load_script_module()
    monkeypatch.setattr(module, "MODULES_ROOT", tmp_path)
    monkeypatch.setattr(module, "SCHEMA_PATH", REAL_SCHEMA_PATH)
    return module


class TestCheckModule:
    """단일 모듈 검사 함수(check_module)의 위반 판정을 확인한다."""

    def test_valid_manifest_has_no_violations(self, tmp_path, script):
        """필수 필드를 모두 채운 manifest 는 위반이 없다."""
        module_dir = tmp_path / "widget"
        module_dir.mkdir()
        (module_dir / "manifest.json").write_text(json.dumps(VALID_MANIFEST), encoding="utf-8")
        schema = json.loads(REAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        assert script.check_module(module_dir, schema) == []

    def test_missing_manifest_file_is_a_violation(self, tmp_path, script):
        """manifest.json 파일 자체가 없으면 위반으로 잡는다."""
        module_dir = tmp_path / "widget"
        module_dir.mkdir()
        schema = json.loads(REAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        violations = script.check_module(module_dir, schema)
        assert len(violations) == 1
        assert "manifest.json 파일이 없습니다" in violations[0]

    def test_manifest_missing_required_field_is_a_violation(self, tmp_path, script):
        """필수 필드(fixtures) 가 빠지면 스키마 위반으로 잡는다."""
        module_dir = tmp_path / "widget"
        module_dir.mkdir()
        incomplete = dict(VALID_MANIFEST)
        del incomplete["fixtures"]
        (module_dir / "manifest.json").write_text(json.dumps(incomplete), encoding="utf-8")
        schema = json.loads(REAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        violations = script.check_module(module_dir, schema)
        assert len(violations) == 1
        assert "스키마를 만족하지 않습니다" in violations[0]

    def test_manifest_invalid_json_is_a_violation(self, tmp_path, script):
        """manifest.json 이 파싱조차 안 되면 위반으로 잡는다."""
        module_dir = tmp_path / "widget"
        module_dir.mkdir()
        (module_dir / "manifest.json").write_text("{not valid json", encoding="utf-8")
        schema = json.loads(REAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        violations = script.check_module(module_dir, schema)
        assert len(violations) == 1
        assert "유효한 JSON 이 아닙니다" in violations[0]


class TestModuleDirs:
    """검사 대상 모듈 디렉토리 목록을 만드는 module_dirs() 를 확인한다."""

    def test_excludes_pycache_directories(self, tmp_path, script):
        """__pycache__ 같은 비모듈 디렉토리는 검사 대상에서 제외한다."""
        (tmp_path / "widget").mkdir()
        (tmp_path / "__pycache__").mkdir()
        names = {path.name for path in script.module_dirs()}
        assert names == {"widget"}

    def test_only_includes_directories(self, tmp_path, script):
        """모듈 루트에 있는 파일(예: 스키마 파일 자체)은 검사 대상에서 제외한다."""
        (tmp_path / "widget").mkdir()
        (tmp_path / "not_a_module.txt").write_text("x", encoding="utf-8")
        names = {path.name for path in script.module_dirs()}
        assert names == {"widget"}


class TestMainAgainstRealRepo:
    """스크립트를 실행해, 스키마 위반뿐 아니라 manifest 자체가 없는 모듈도 QA 에서
    잡아내는지 확인한다 (태스크 노트 요구사항). manifest 누락 감지는 실제 저장소의
    특정 모듈 상태에 의존하지 않도록 합성 모듈 루트로 검증한다."""

    def test_main_reports_module_missing_manifest(self, tmp_path, monkeypatch, capsys):
        """manifest.json 이 없는 모듈은 위반으로 보고되고 종료 코드 1 을 반환한다."""
        module = _load_script_module()
        (tmp_path / "widget").mkdir()
        (tmp_path / "widget" / "manifest.json").write_text(
            json.dumps(VALID_MANIFEST), encoding="utf-8"
        )
        (tmp_path / "orphan").mkdir()  # manifest.json 없음 → 위반이어야 한다
        monkeypatch.setattr(module, "MODULES_ROOT", tmp_path)
        monkeypatch.setattr(module, "SCHEMA_PATH", REAL_SCHEMA_PATH)
        exit_code = module.main()
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "orphan" in captured.err
        assert "manifest.json 파일이 없습니다" in captured.err

    def test_modules_with_manifest_individually_pass(self, monkeypatch):
        """manifest.json 을 가진 모듈들은 개별적으로 필수 필드 검증을 통과한다."""
        module = _load_script_module()
        monkeypatch.chdir(REPO_ROOT)
        schema = json.loads(module.SCHEMA_PATH.read_text(encoding="utf-8"))
        modules_with_manifest = [
            module_dir
            for module_dir in module.module_dirs()
            if (module_dir / "manifest.json").is_file()
        ]
        assert modules_with_manifest, "적어도 하나의 모듈은 manifest 를 가져야 한다"
        for module_dir in modules_with_manifest:
            assert module.check_module(module_dir, schema) == [], module_dir.name
