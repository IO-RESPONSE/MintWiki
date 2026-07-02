"""jobs 모듈 계약 manifest(`src/modules/jobs/manifest.json`) 검증.

`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 고정한 스키마를 따르는지 확인한다.
jobs 모듈은 다른 모듈(cache, discussion 등)과 달리 아직 Python 구현이 없으므로
(README.md 만 존재), 이 테스트는 실제 서비스/저장소 클래스와의 일치가 아니라
manifest 자체의 형식과 shared hosting sync fallback 계약 서술을 검증한다.
태스크 0362 의 산출물이다.
"""
import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODULE_PATH = REPO_ROOT / "src" / "modules" / "jobs"
MANIFEST_PATH = MODULE_PATH / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestJobsManifest:
    """jobs manifest 파일 자체의 형식과 스키마 준수를 검증한다."""

    def test_manifest_exists(self):
        """manifest 파일이 모듈 디렉터리 아래에 존재한다."""
        assert MANIFEST_PATH.is_file()

    def test_manifest_is_valid_json(self):
        """manifest 가 유효한 JSON 이다."""
        _load_manifest()

    def test_manifest_conforms_to_schema(self):
        """manifest 가 module_manifest.schema.json 을 만족한다."""
        manifest = _load_manifest()
        schema = _load_schema()
        jsonschema.validate(instance=manifest, schema=schema)

    def test_manifest_module_name_matches_directory(self):
        """module 필드가 src/modules/jobs 디렉터리 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["module"] == "jobs"

    def test_manifest_port_source_path_matches_module(self):
        """port.source_path 가 이 모듈 디렉터리를 가리킨다."""
        manifest = _load_manifest()
        assert manifest["port"]["source_path"] == "src/modules/jobs"

    def test_manifest_port_status_is_not_started(self):
        """구현이 아직 없으므로 port.status 는 not_started 여야 한다."""
        manifest = _load_manifest()
        assert manifest["port"]["status"] == "not_started"


class TestJobsManifestReflectsMissingImplementation:
    """jobs 는 아직 구현이 없는 모듈이므로, manifest 가 이 사실을 정직하게
    반영하는지 확인한다 (다른 모듈처럼 존재하지 않는 구현을 서술하지 않는지)."""

    def test_service_path_does_not_exist_yet(self):
        """service.path 가 가리키는 파일은 아직 생성되지 않았다."""
        manifest = _load_manifest()
        assert not (REPO_ROOT / manifest["service"]["path"]).is_file()

    def test_repository_path_does_not_exist_yet(self):
        """repository.port_path 가 가리키는 파일은 아직 생성되지 않았다."""
        manifest = _load_manifest()
        assert not (REPO_ROOT / manifest["repository"]["port_path"]).is_file()

    def test_only_readme_exists_in_module_directory(self):
        """모듈 디렉터리에는 README.md 와 manifest.json 외 구현 파일이 없다."""
        top_level_files = {p.name for p in MODULE_PATH.iterdir() if p.is_file()}
        assert top_level_files == {"README.md", "manifest.json"}

    def test_contract_notes_disclose_missing_implementation(self):
        """contract_notes 가 구현 부재 사실을 명시한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "아직 Python 구현이 없다" in notes


class TestJobsManifestSharedHostingContract:
    """태스크 노트가 요구하는 'shared hosting 에서는 sync fallback 이 기본'
    계약이 manifest 에 명시되어 있는지 확인한다."""

    def test_contract_notes_declare_sync_fallback_default_on_shared_hosting(self):
        """contract_notes 가 shared hosting 에서의 sync 기본 동작을 서술한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "shared hosting" in notes
        assert "sync" in notes
        assert "기본" in notes

    def test_run_sync_is_declared_as_public_method(self):
        """sync 러너 진입점(run_sync)이 공개 계약 메서드로 선언되어 있다."""
        manifest = _load_manifest()
        assert "run_sync" in manifest["service"]["public_methods"]
