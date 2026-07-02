"""제목 정규화 공용 fixture 기반 테스트.

`tests/modules/document/fixtures/` 아래 교차언어 fixture(0369,
`docs/cross-language-fixture-schema.md`)를 읽어 `normalize_title` 을
검증한다. 같은 fixture 파일을 이후 PHP 포트(0426)가 재사용한다.
"""
import json
from pathlib import Path

import jsonschema
import pytest

from modules.document.title import EmptyTitleError, normalize_title

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "modules" / "document" / "fixtures"
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "document" / "manifest.json"
SCHEMA_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "schema" / "cross_language_fixture.schema.json"
)

FIXTURE_FILES = sorted(FIXTURES_DIR.glob("*.json"))


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixtures_directory_matches_manifest():
    """manifest.json 의 fixtures.path/format 이 실제 디렉터리와 일치한다."""
    manifest = _load_json(MANIFEST_PATH)
    assert manifest["fixtures"]["path"] == "tests/modules/document/fixtures"
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
def test_normalize_title_matches_fixture(fixture_path):
    """normalize_title 의 실제 동작이 fixture 의 expected/errors 와 일치한다."""
    data = _load_json(fixture_path)
    title = data["input"]["title"]

    if data["errors"]:
        assert data["expected"] is None
        with pytest.raises(EmptyTitleError):
            normalize_title(title)
    else:
        assert normalize_title(title) == data["expected"]["title"]
