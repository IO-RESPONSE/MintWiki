"""파서 공용 교차언어 fixture 기반 테스트.

`tests/modules/parser/fixtures/` 아래 교차언어 fixture(0369,
`docs/cross-language-fixture-schema.md`)를 읽어 `PlainTextBlockParser.parse`
를 검증한다. 정규식 문법은 Python `re` 와 PHP PCRE 가 다를 수 있으므로,
이후 PHP 포트가 같은 fixture 를 재사용해 두 언어의 파싱 결과가 같은지
검증할 수 있다.
"""
import json
from pathlib import Path

import jsonschema
import pytest

from modules.parser import PlainTextBlockParser

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "modules" / "parser" / "fixtures"
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "parser" / "manifest.json"
SCHEMA_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "schema" / "cross_language_fixture.schema.json"
)

FIXTURE_FILES = sorted(FIXTURES_DIR.glob("*.json"))


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixtures_directory_matches_manifest():
    """manifest.json 의 fixtures.path/format 이 실제 디렉터리와 일치한다."""
    manifest = _load_json(MANIFEST_PATH)
    assert manifest["fixtures"]["path"] == "tests/modules/parser/fixtures"
    assert manifest["fixtures"]["format"] == "json"


def test_fixtures_directory_is_not_empty():
    """fixture 가 최소 1개 이상 채워져 있다."""
    assert FIXTURE_FILES


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=lambda p: p.stem)
def test_fixture_conforms_to_cross_language_schema(fixture_path):
    """각 fixture 파일이 교차언어 fixture JSON Schema를 만족한다."""
    schema = _load_json(SCHEMA_PATH)
    data = _load_json(fixture_path)
    jsonschema.validate(instance=data, schema=schema)


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=lambda p: p.stem)
def test_parse_matches_fixture(fixture_path):
    """parse() 의 실제 동작이 fixture 의 expected/errors 와 일치한다."""
    data = _load_json(fixture_path)
    source = data["input"]["source"]

    assert data["errors"] == []
    result = PlainTextBlockParser.parse(source)
    assert result.blocks == data["expected"]["blocks"]
    assert result.metadata == data["expected"]["metadata"]
