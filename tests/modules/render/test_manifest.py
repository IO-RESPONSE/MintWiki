"""render 모듈 계약 manifest(`src/modules/render/manifest.json`) 검증.

`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 고정한 스키마를 따르는지,
그리고 manifest 가 가리키는 서비스 계약이 실제 구현과 어긋나지 않는지,
XSS 이스케이프 책임 경계가 render 모듈에 있는지 확인한다. 태스크 0357 의
산출물이다.
"""
import inspect
import json
from pathlib import Path

import jsonschema

import modules.render as render_module

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "render" / "manifest.json"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"

# render 모듈이 재노출하는 도메인 모델 클래스는 데이터 구조이지 계약
# 메서드가 아니므로 public_methods 비교에서 제외한다.
MODEL_CLASS_NAMES = {"RenderResult", "RenderMetadata", "Heading", "Footnote"}


def _load_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestRenderManifest:
    """render manifest 파일 자체의 형식과 스키마 준수를 검증한다."""

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
        """module 필드가 src/modules/render 디렉터리 이름과 일치한다."""
        manifest = _load_manifest()
        assert manifest["module"] == "render"

    def test_manifest_port_source_path_matches_module(self):
        """port.source_path 가 이 모듈 디렉터리를 가리킨다."""
        manifest = _load_manifest()
        assert manifest["port"]["source_path"] == "src/modules/render"

    def test_manifest_port_status_not_ready_yet(self):
        """계약만 고정된 단계이므로 status 는 ready 가 아니다."""
        manifest = _load_manifest()
        assert manifest["port"]["status"] in {"not_started", "in_progress"}


class TestRenderManifestMatchesImplementation:
    """manifest 가 선언한 계약이 실제 구현과 어긋나지 않는지 확인한다."""

    def test_service_path_is_importable(self):
        """service.path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["service"]["path"]).is_file()

    def test_public_methods_exist_on_service(self):
        """manifest 에 선언된 공개 함수가 modules.render 패키지에 실제로 존재한다."""
        manifest = _load_manifest()
        for method_name in manifest["service"]["public_methods"]:
            assert hasattr(render_module, method_name), (
                f"modules.render 에 {method_name} 함수가 없습니다"
            )

    def test_no_undeclared_public_methods(self):
        """render 패키지가 재노출하는 함수가 manifest 에 모두 선언되어 있다
        (도메인 모델 클래스는 계약 메서드가 아니므로 제외한다)."""
        manifest = _load_manifest()
        declared = set(manifest["service"]["public_methods"])
        actual = {
            name
            for name in render_module.__all__
            if name not in MODEL_CLASS_NAMES and not inspect.isclass(getattr(render_module, name))
        }
        assert actual == declared

    def test_repository_path_is_importable(self):
        """repository.port_path 가 실제 존재하는 파일을 가리킨다."""
        manifest = _load_manifest()
        assert (REPO_ROOT / manifest["repository"]["port_path"]).is_file()

    def test_repository_interface_matches_render_entry_point(self):
        """render 는 저장소도 단일 진입 클래스도 없으므로 repository.interface 는
        모듈 이름 자체(공개 함수 재노출 지점)와 일치해야 한다."""
        manifest = _load_manifest()
        assert manifest["repository"]["interface"] == "render"


class TestRenderManifestEscapeBoundary:
    """XSS 이스케이프 책임 경계가 render 모듈에 명시되어 있는지 확인한다."""

    def test_contract_notes_declare_escape_ownership(self):
        """contract_notes 가 이스케이프 책임이 render 에 있다고 명시한다."""
        manifest = _load_manifest()
        notes = " ".join(manifest.get("contract_notes", []))
        assert "이스케이프" in notes
        assert "render" in notes

    def test_escape_html_is_declared_public_contract(self):
        """이스케이프 경계를 이루는 세 살균 함수가 모두 공개 계약에 선언되어 있다."""
        manifest = _load_manifest()
        declared = set(manifest["service"]["public_methods"])
        assert {"escape_html", "sanitize_url", "sanitize_css_value"} <= declared

    def test_escape_html_neutralizes_html_special_characters(self):
        """escape_html 이 실제로 HTML 특수 문자를 이스케이프해 XSS 를 막는다."""
        payload = "<script>alert('xss')</script>"
        escaped = render_module.escape_html(payload)
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped
