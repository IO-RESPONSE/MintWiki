"""`docs/cross-language-fixture-schema.md` 와
`tests/fixtures/schema/cross_language_fixture.schema.json` 이 태스크 0369 의
Notes 요구사항(input/expected/errors 구조 고정)을 유지하는지 확인한다.
"""
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "cross-language-fixture-schema.md"
SCHEMA_PATH = REPO_ROOT / "tests" / "fixtures" / "schema" / "cross_language_fixture.schema.json"
EXAMPLES_DIR = REPO_ROOT / "tests" / "fixtures" / "schema" / "examples"

REQUIRED_DOC_HEADINGS = [
    "## 스키마 정의 위치",
    "## 최상위 구조: `input` / `expected` / `errors`",
    "### `input`",
    "### `expected`",
    "### `errors`",
]

REQUIRED_TOP_LEVEL_FIELDS = ["schema_version", "input", "expected", "errors"]


def test_cross_language_fixture_schema_doc_exists():
    """교차언어 fixture 스키마 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_cross_language_fixture_schema_doc_has_required_sections():
    """input/expected/errors 구조 설명이 모두 문서화되어 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_cross_language_fixture_schema_doc_references_related_docs():
    """기존 glossary/디렉터리 규칙 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/fixture-directory-convention.md" in content
    assert "docs/portability-glossary.md" in content
    assert "docs/php-replacement-strategy.md" in content
    assert "tests/fixtures/schema/cross_language_fixture.schema.json" in content


def test_cross_language_fixture_schema_json_exists():
    """기계 판독 가능한 JSON Schema 파일이 tests/fixtures/schema 아래에 존재한다."""
    assert SCHEMA_PATH.is_file()


def test_cross_language_fixture_schema_json_is_valid_json():
    """스키마 파일이 유효한 JSON 이다."""
    json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_cross_language_fixture_schema_json_declares_required_fields():
    """schema_version, input, expected, errors 필드가 스키마에 있다."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["required"] == REQUIRED_TOP_LEVEL_FIELDS
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in schema["properties"], f"missing schema property: {field}"
    assert schema["additionalProperties"] is False


def test_cross_language_fixture_schema_json_errors_field_is_string_array():
    """errors 필드는 안정적인 error code 문자열 배열이어야 한다(메시지 문자열 금지)."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors_schema = schema["properties"]["errors"]
    assert errors_schema["type"] == "array"
    assert errors_schema["items"]["type"] == "string"


def test_cross_language_fixture_schema_json_examples_match_required_fields():
    """스키마에 포함된 예시가 스스로 선언한 필수 필드를 모두 채운다."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    examples = schema.get("examples", [])
    assert examples, "schema must ship at least one example fixture"
    for example in examples:
        for field in REQUIRED_TOP_LEVEL_FIELDS:
            assert field in example, f"example fixture missing field: {field}"
        jsonschema.validate(instance=example, schema=schema)


@pytest.mark.parametrize(
    "example_path",
    sorted(EXAMPLES_DIR.glob("*.json")) if EXAMPLES_DIR.is_dir() else [],
)
def test_example_fixture_files_satisfy_schema(example_path):
    """tests/fixtures/schema/examples 의 예시 fixture 파일이 스키마를 만족한다."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    instance = json.loads(example_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=instance, schema=schema)


def test_example_fixtures_directory_has_success_and_error_case():
    """expected/errors 상호배타 규칙을 보여주는 성공/실패 예시가 각각 존재한다."""
    assert (EXAMPLES_DIR / "success_example.json").is_file()
    assert (EXAMPLES_DIR / "error_example.json").is_file()

    success = json.loads((EXAMPLES_DIR / "success_example.json").read_text(encoding="utf-8"))
    assert success["errors"] == []
    assert success["expected"] is not None

    error_case = json.loads((EXAMPLES_DIR / "error_example.json").read_text(encoding="utf-8"))
    assert error_case["expected"] is None
    assert len(error_case["errors"]) >= 1
