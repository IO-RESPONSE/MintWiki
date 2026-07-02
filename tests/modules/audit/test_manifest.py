"""audit 모듈 계약 manifest(`src/modules/audit/manifest.json`) 검증.

`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 고정한 스키마를 따르는지 확인한다.
audit 모듈은 jobs 모듈과 마찬가지로 아직 Python 구현이 없으므로(README.md 만
존재), 이 테스트는 실제 서비스/저장소 클래스와의 일치가 아니라 manifest 자체의
형식과 append-only 계약/실패 정책 서술을 검증한다. 태스크 0363 의 산출물이다.
"""
import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODULE_PATH = REPO_ROOT / "src" / "modules" / "audit"
MANIFEST_PATH = MODULE_PATH / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestAuditManifest:
    """audit manifest 파일 자체의 형식과 스키마 준수를 검증한다."""

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
        """module 필드가 src/modules/audit 디렉터리 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["module"] == "audit"

    def test_manifest_port_source_path_matches_module(self):
        """port.source_path 가 이 모듈 디렉터리를 가리킨다."""
        manifest = _load_manifest()
        assert manifest["port"]["source_path"] == "src/modules/audit"

    def test_manifest_port_status_is_not_started(self):
        """구현이 아직 없으므로 port.status 는 not_started 여야 한다."""
        manifest = _load_manifest()
        assert manifest["port"]["status"] == "not_started"


class TestAuditManifestReflectsMissingImplementation:
    """audit 는 아직 구현이 없는 모듈이므로, manifest 가 이 사실을 정직하게
    반영하는지 확인한다 (다른 모듈처럼 존재하지 않는 구현을 서술하지 않는지)."""

    def test_service_path_does_not_exist_yet(self):
        """service.path 가 가리키는 파일은 아직 생성되지 않았다."""
        manifest = _load_manifest()
        assert not (REPO_ROOT / manifest["service"]["path"]).is_file()

    def test_repository_path_does_not_exist_yet(self):
        """repository.port_path 가 가리키는 파일은 아직 생성되지 않았다."""
        manifest = _load_manifest()
        assert not (REPO_ROOT / manifest["repository"]["port_path"]).is_file()

    def test_only_readme_and_manifest_exist_in_module_directory(self):
        """모듈 디렉터리에는 README.md 와 manifest.json 외 구현 파일이 없다."""
        top_level_files = {p.name for p in MODULE_PATH.iterdir() if p.is_file()}
        assert top_level_files == {"README.md", "manifest.json"}

    def test_contract_notes_disclose_missing_implementation(self):
        """contract_notes 가 구현 부재 사실을 명시한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "아직 Python 구현이 없다" in notes


class TestAuditManifestAppendOnlyContract:
    """태스크 노트가 요구하는 'append-only 계약과 실패 정책'이 manifest 에
    고정되어 있는지 확인한다."""

    def test_contract_notes_declare_append_only_write_path(self):
        """contract_notes 가 append-only 계약(수정/삭제 없음)을 서술한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "append-only" in notes
        assert "삭제" in notes

    def test_contract_notes_declare_failure_policy(self):
        """contract_notes 가 저장 실패 시 예외를 전파해야 한다는 실패 정책을
        서술한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "실패 정책" in notes
        assert "예외" in notes

    def test_record_is_declared_as_public_method(self):
        """append 전용 쓰기 진입점(record)이 공개 계약 메서드로 선언되어
        있다."""
        manifest = _load_manifest()
        assert "record" in manifest["service"]["public_methods"]

    def test_service_contract_has_no_mutation_or_deletion_methods(self):
        """서비스 계약에 이벤트를 수정하거나 삭제하는 메서드가 없다."""
        manifest = _load_manifest()
        methods = manifest["service"]["public_methods"]
        forbidden = {"update", "update_event", "delete", "delete_event", "remove"}
        assert not (set(methods) & forbidden)


class TestAuditManifestDependencyDirection:
    """docs/modules.md 의 'audit 은 business module 을 호출하지 않는다'는
    의존 방향 규칙이 manifest 에 명시되어 있는지 확인한다."""

    def test_contract_notes_declare_no_business_module_calls(self):
        """contract_notes 가 audit -> business module 호출 금지를
        서술한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "business module" in notes
