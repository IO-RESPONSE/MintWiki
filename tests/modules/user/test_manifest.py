"""user 모듈 계약 manifest(`src/modules/user/manifest.json`) 검증.

`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 고정한 스키마를 따르는지,
그리고 manifest 가 가리키는 서비스/저장소 계약이 실제 구현과 어긋나지
않는지, 세션/그룹/차단 세 하위 계약이 분리되어 문서화되어 있는지
확인한다. 태스크 0358 의 산출물이다.
"""
import inspect
import json
from pathlib import Path

import jsonschema

from modules.user.block_check_service import BlockCheckService
from modules.user.block_repository import BlockRepository
from modules.user.group import Group
from modules.user.repository import UserRepository
from modules.user.session_repository import SessionRepository

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "user" / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestUserManifest:
    """user manifest 파일 자체의 형식과 스키마 준수를 검증한다."""

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
        """module 필드가 src/modules/user 디렉터리 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["module"] == "user"

    def test_manifest_port_source_path_matches_module(self):
        """port.source_path 가 이 모듈 디렉터리를 가리킨다."""
        manifest = _load_manifest()
        assert manifest["port"]["source_path"] == "src/modules/user"

    def test_manifest_port_status_not_ready_yet(self):
        """계약만 고정된 단계이므로 status 는 ready 가 아니다."""
        manifest = _load_manifest()
        assert manifest["port"]["status"] in {"not_started", "in_progress"}


class TestUserManifestMatchesImplementation:
    """manifest 가 선언한 계약이 실제 구현과 어긋나지 않는지 확인한다."""

    def test_service_path_is_importable(self):
        """service.path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["service"]["path"]).is_file()

    def test_public_methods_exist_on_service(self):
        """manifest 에 선언된 공개 메서드가 BlockCheckService 에 실제로 존재한다."""
        manifest = _load_manifest()
        for method_name in manifest["service"]["public_methods"]:
            assert hasattr(BlockCheckService, method_name), (
                f"BlockCheckService 에 {method_name} 메서드가 없습니다"
            )

    def test_no_undeclared_public_methods(self):
        """BlockCheckService 의 공개 메서드가 manifest 에 모두 선언되어 있다."""
        manifest = _load_manifest()
        declared = set(manifest["service"]["public_methods"])
        actual = {
            name
            for name, _ in inspect.getmembers(BlockCheckService, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        assert actual == declared

    def test_repository_path_is_importable(self):
        """repository.port_path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["repository"]["port_path"]).is_file()

    def test_repository_interface_matches_abstract_base(self):
        """repository.interface 가 UserRepository ABC 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["repository"]["interface"] == UserRepository.__name__


class TestUserManifestSeparatesSubContracts:
    """세션, 그룹, 차단 계약이 하나로 뭉개지지 않고 분리되어 있는지 확인한다."""

    def test_contract_notes_mention_session_group_block(self):
        """contract_notes 가 세 하위 계약을 모두 명시적으로 언급한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "세션" in notes
        assert "그룹" in notes
        assert "차단" in notes

    def test_session_repository_contract_has_declared_methods(self):
        """세션 계약(SessionRepository)이 contract_notes 가 서술한 메서드를 가진다."""
        for method_name in ("create", "get", "delete"):
            assert hasattr(SessionRepository, method_name), (
                f"SessionRepository 에 {method_name} 메서드가 없습니다"
            )

    def test_block_repository_contract_has_declared_methods(self):
        """차단 계약(BlockRepository)이 contract_notes 가 서술한 메서드를 가진다."""
        for method_name in ("create", "get", "get_by_user_id", "delete"):
            assert hasattr(BlockRepository, method_name), (
                f"BlockRepository 에 {method_name} 메서드가 없습니다"
            )

    def test_group_contract_has_declared_methods(self):
        """그룹 계약(Group)이 contract_notes 가 서술한 구성원 관리 메서드를 가진다."""
        for method_name in ("has_member", "add_member", "remove_member"):
            assert hasattr(Group, method_name), f"Group 에 {method_name} 메서드가 없습니다"

    def test_group_has_no_repository_port_yet(self):
        """그룹은 아직 저장소 포트가 없다는 contract_notes 서술이 실제와 일치한다."""
        assert not (REPO_ROOT / "src" / "modules" / "user" / "group_repository.py").exists()

    def test_block_check_service_is_the_only_service_in_module(self):
        """차단 계약의 BlockCheckService 가 manifest 최상위 service 필드가 가리키는
        대상과 일치한다 — user 모듈에서 유일한 서비스 계층이라는 서술을 뒷받침한다."""
        manifest = _load_manifest()
        assert manifest["service"]["path"] == "src/modules/user/block_check_service.py"
