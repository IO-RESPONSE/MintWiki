"""admin 모듈 계약 manifest(`src/modules/admin/manifest.json`) 검증.

`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 고정한 스키마를 따르는지 확인한다.
admin 모듈은 audit/jobs 모듈과 마찬가지로 아직 Python 구현이 없으므로(README.md 만
존재), 이 테스트는 실제 서비스/저장소 클래스와의 일치가 아니라 manifest 자체의
형식과 '관리자 액션은 audit hook을 통과해야 한다'는 태스크 노트 요구사항을
검증한다. 태스크 0364 의 산출물이다.
"""
import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODULE_PATH = REPO_ROOT / "src" / "modules" / "admin"
MANIFEST_PATH = MODULE_PATH / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestAdminManifest:
    """admin manifest 파일 자체의 형식과 스키마 준수를 검증한다."""

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
        """module 필드가 src/modules/admin 디렉터리 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["module"] == "admin"

    def test_manifest_port_source_path_matches_module(self):
        """port.source_path 가 이 모듈 디렉터리를 가리킨다."""
        manifest = _load_manifest()
        assert manifest["port"]["source_path"] == "src/modules/admin"

    def test_manifest_port_status_is_not_started(self):
        """구현이 아직 없으므로 port.status 는 not_started 여야 한다."""
        manifest = _load_manifest()
        assert manifest["port"]["status"] == "not_started"


class TestAdminManifestReflectsMissingImplementation:
    """admin 은 아직 구현이 없는 모듈이므로, manifest 가 이 사실을 정직하게
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


class TestAdminManifestAuditHookContract:
    """태스크 노트가 요구하는 '관리자 액션은 audit hook을 통과해야 함'이
    manifest 에 고정되어 있는지 확인한다."""

    def test_contract_notes_declare_audit_hook_requirement(self):
        """contract_notes 가 관리자 액션의 audit hook 통과 의무를 서술한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "audit hook" in notes

    def test_contract_notes_forbid_silently_skipping_audit(self):
        """audit 기록을 건너뛰고 조용히 성공시키는 경로가 금지됨을 서술한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "건너뛰고" in notes
        assert "금지" in notes

    def test_all_public_methods_are_admin_actions_covered_by_audit_hook(self):
        """공개 메서드 각각이 contract_notes 의 audit hook 서술에 이름으로
        포함되어, 어떤 관리자 액션도 예외 없이 audit hook 대상임을 확인한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        for method in manifest["service"]["public_methods"]:
            assert method in notes, f"{method} not referenced in contract_notes"


class TestAdminManifestDependencyDirection:
    """docs/modules.md 의 'admin 은 acl, user, document, discussion, audit 을
    호출할 수 있다'는 의존 방향 규칙이 manifest 에 명시되어 있는지 확인한다."""

    def test_contract_notes_declare_allowed_dependencies(self):
        """contract_notes 가 admin 이 호출 가능한 모듈 목록을 서술한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        for dependency in ("acl", "user", "document", "discussion", "audit"):
            assert dependency in notes
