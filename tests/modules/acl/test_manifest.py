"""acl 모듈 계약 manifest(`src/modules/acl/manifest.json`) 검증.

`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 고정한 스키마를 따르는지,
그리고 manifest 가 가리키는 서비스 계약(check 의 입력/출력 모델)이 실제
구현과 어긋나지 않는지 확인한다. 태스크 0359 의 산출물이다.
"""
import inspect
import json
from pathlib import Path

import jsonschema

from modules.acl.decision import Decision
from modules.acl.permission import Permission
from modules.acl.rule import SubjectType
from modules.acl.service import AclService

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "acl" / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestAclManifest:
    """acl manifest 파일 자체의 형식과 스키마 준수를 검증한다."""

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
        """module 필드가 src/modules/acl 디렉터리 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["module"] == "acl"

    def test_manifest_port_source_path_matches_module(self):
        """port.source_path 가 이 모듈 디렉터리를 가리킨다."""
        manifest = _load_manifest()
        assert manifest["port"]["source_path"] == "src/modules/acl"

    def test_manifest_port_status_not_ready_yet(self):
        """계약만 고정된 단계이므로 status 는 ready 가 아니다."""
        manifest = _load_manifest()
        assert manifest["port"]["status"] in {"not_started", "in_progress"}


class TestAclManifestMatchesImplementation:
    """manifest 가 선언한 계약이 실제 구현과 어긋나지 않는지 확인한다."""

    def test_service_path_is_importable(self):
        """service.path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["service"]["path"]).is_file()

    def test_public_methods_exist_on_service(self):
        """manifest 에 선언된 공개 메서드가 AclService 에 실제로 존재한다."""
        manifest = _load_manifest()
        for method_name in manifest["service"]["public_methods"]:
            assert hasattr(AclService, method_name), (
                f"AclService 에 {method_name} 메서드가 없습니다"
            )

    def test_no_undeclared_public_methods(self):
        """AclService 의 공개 메서드가 manifest 에 모두 선언되어 있다."""
        manifest = _load_manifest()
        declared = set(manifest["service"]["public_methods"])
        actual = {
            name
            for name, _ in inspect.getmembers(AclService, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        assert actual == declared

    def test_repository_path_is_importable(self):
        """repository.port_path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["repository"]["port_path"]).is_file()

    def test_repository_interface_matches_acl_entry_point(self):
        """acl 은 저장소 포트(ABC)가 아직 없으므로 repository.interface 는
        유일한 진입 계약인 AclService 이름과 일치해야 한다."""
        manifest = _load_manifest()
        assert manifest["repository"]["interface"] == AclService.__name__


class TestAclManifestDecisionContract:
    """check() 의 입력/출력 모델이 manifest 가 고정한 계약과 일치하는지 확인한다."""

    def test_contract_notes_declare_check_signature(self):
        """contract_notes 가 check() 의 고정된 입력/출력 계약을 명시한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "check(" in notes
        assert "Decision" in notes

    def test_check_returns_decision_with_fixed_fields(self):
        """check() 는 permission/allowed/reason/matched_rule_id 를 가진
        Decision 을 반환한다."""
        service = AclService()
        decision = service.check(
            permission=Permission.READ,
            subject_type=SubjectType.ALL,
        )
        assert isinstance(decision, Decision)
        assert decision.permission is Permission.READ
        assert decision.allowed is False
        assert decision.reason == "acl.no_matching_rule"
        assert decision.matched_rule_id is None
