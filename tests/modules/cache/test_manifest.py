"""cache 모듈 계약 manifest(`src/modules/cache/manifest.json`) 검증.

`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 고정한 스키마를 따르는지,
그리고 manifest 가 가리키는 서비스/포트 계약(Cache, CacheBackend 와 그
어댑터들)이 실제 구현과 어긋나지 않는지 확인한다. 태스크 0361 의 산출물이다.
"""
import inspect
import json
from pathlib import Path

import jsonschema

from modules.cache.backend import CacheBackend, InMemoryCacheBackend
from modules.cache.cache import Cache
from modules.cache.redis import RedisCacheBackend

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "cache" / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestCacheManifest:
    """cache manifest 파일 자체의 형식과 스키마 준수를 검증한다."""

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
        """module 필드가 src/modules/cache 디렉터리 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["module"] == "cache"

    def test_manifest_port_source_path_matches_module(self):
        """port.source_path 가 이 모듈 디렉터리를 가리킨다."""
        manifest = _load_manifest()
        assert manifest["port"]["source_path"] == "src/modules/cache"

    def test_manifest_port_status_not_ready_yet(self):
        """계약만 고정된 단계이므로 status 는 ready 가 아니다."""
        manifest = _load_manifest()
        assert manifest["port"]["status"] in {"not_started", "in_progress"}


class TestCacheManifestMatchesImplementation:
    """manifest 가 선언한 계약이 실제 구현과 어긋나지 않는지 확인한다."""

    def test_service_path_is_importable(self):
        """service.path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["service"]["path"]).is_file()

    def test_public_methods_exist_on_service(self):
        """manifest 에 선언된 공개 메서드가 Cache 에 실제로 존재한다."""
        manifest = _load_manifest()
        for method_name in manifest["service"]["public_methods"]:
            assert hasattr(Cache, method_name), (
                f"Cache 에 {method_name} 메서드가 없습니다"
            )

    def test_no_undeclared_public_methods(self):
        """Cache 의 공개 메서드가 manifest 에 모두 선언되어 있다."""
        manifest = _load_manifest()
        declared = set(manifest["service"]["public_methods"])
        actual = {
            name
            for name, _ in inspect.getmembers(Cache, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        assert actual == declared

    def test_repository_path_is_importable(self):
        """repository.port_path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["repository"]["port_path"]).is_file()

    def test_repository_interface_matches_cache_backend_abc(self):
        """repository.interface 가 CacheBackend ABC 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["repository"]["interface"] == CacheBackend.__name__

    def test_adapter_path_is_importable(self):
        """repository.adapter_path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        adapter_path = manifest["repository"].get("adapter_path")
        assert adapter_path is not None
        assert (REPO_ROOT / adapter_path).is_file()

    def test_both_adapters_implement_the_declared_port(self):
        """in-memory 와 redis 어댑터 모두 선언된 CacheBackend 를 구현한다."""
        assert issubclass(InMemoryCacheBackend, CacheBackend)
        assert issubclass(RedisCacheBackend, CacheBackend)


class TestCacheManifestBackendPortContract:
    """cache backend 포트가 TTL/메트릭 없이 get/set/delete/clear 네 개의
    최소 계약만 요구한다는 사실이 manifest 서술과 실제 구현에서 일치하는지
    확인한다."""

    def test_contract_notes_describe_ttl_and_metrics_gap(self):
        """contract_notes 가 TTL/메트릭 훅 미구현 사실을 명시한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "TTL" in notes
        assert "메트릭" in notes

    def test_contract_notes_describe_render_not_wired(self):
        """contract_notes 가 render 가 아직 cache 를 호출하지 않는다는
        사실을 명시한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "render" in notes

    def test_backend_port_has_exactly_four_abstract_methods(self):
        """CacheBackend 는 get/set/delete/clear 네 개의 추상 메서드만
        요구하며 TTL 파라미터는 시그니처에 없다."""
        assert CacheBackend.__abstractmethods__ == frozenset(
            {"get", "set", "delete", "clear"}
        )
        get_params = list(inspect.signature(CacheBackend.get).parameters)
        assert "ttl" not in get_params
        set_params = list(inspect.signature(CacheBackend.set).parameters)
        assert "ttl" not in set_params
