"""`docs/module-contract-manifest-schema.md` 와
`src/modules/module_manifest.schema.json` 이 요구사항(port, service,
repository, fixture 위치 선언)을 유지하는지 확인한다.

이 문서/스키마는 태스크 0353 의 산출물이며, 이후 태스크(0354-0366)가
개별 모듈 manifest 와 검증 스크립트를 채울 때 기준으로 삼는다. 필수 필드가
실수로 삭제되지 않도록 회귀 테스트로 고정한다.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "module-contract-manifest-schema.md"
SCHEMA_PATH = REPO_ROOT / "src" / "modules" / "module_manifest.schema.json"

REQUIRED_DOC_HEADINGS = [
    "## 스키마 정의 위치",
    "## manifest 파일 위치 규칙",
    "## 필수 필드",
    "### `port`",
    "### `service`",
    "### `repository`",
    "### `fixtures`",
]

REQUIRED_TOP_LEVEL_FIELDS = [
    "schema_version",
    "module",
    "summary",
    "port",
    "service",
    "repository",
    "fixtures",
]


def test_module_manifest_schema_doc_exists():
    """manifest 스키마 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_module_manifest_schema_doc_has_required_sections():
    """Notes 에서 요구한 port/service/repository/fixture 위치 선언이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_module_manifest_schema_doc_references_related_docs():
    """기존 계약 문서들과 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/portability-glossary.md" in content
    assert "docs/modules.md" in content
    assert "src/modules/module_manifest.schema.json" in content


def test_module_manifest_schema_json_exists():
    """기계 판독 가능한 JSON Schema 파일이 src/modules 아래에 존재한다."""
    assert SCHEMA_PATH.is_file()


def test_module_manifest_schema_json_is_valid_json():
    """스키마 파일이 유효한 JSON 이다."""
    json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_module_manifest_schema_json_declares_required_fields():
    """port, service, repository, fixtures 위치를 선언하는 필수 필드가 스키마에 있다."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["required"] == REQUIRED_TOP_LEVEL_FIELDS
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in schema["properties"], f"missing schema property: {field}"


def test_module_manifest_schema_json_example_matches_required_fields():
    """스키마에 포함된 예시가 스스로 선언한 필수 필드를 모두 채운다."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    examples = schema.get("examples", [])
    assert examples, "schema must ship at least one example manifest"
    example = examples[0]
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in example, f"example manifest missing field: {field}"
    assert example["port"]["status"] in {"not_started", "in_progress", "ready"}
    assert example["fixtures"]["format"] == "json"
