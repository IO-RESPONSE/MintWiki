"""render 모듈 공용 교차언어 fixture 기반 테스트.

`tests/modules/render/fixtures/` 아래 `*.json` 교차언어 fixture(0369,
`docs/cross-language-fixture-schema.md`)를 읽어 render 모듈의 살균 경계
함수(escape_html/sanitize_url/sanitize_css_value)와 이들에 의존하는
대표 렌더 함수(generate_heading_id/render_bold/render_heading)를
검증한다. 기존 `tests/modules/render/fixtures/*.html` 스냅샷과 이를 쓰는
`FixtureRunner` 기반 테스트는 그대로 유지되며, 이 파일은 그 위에 PHP
포트가 재사용할 수 있는 언어 독립 fixture 를 추가한다.

fixture 파일명은 `<함수명>__<시나리오>.json` 형식을 따르며, `__` 앞
부분으로 대상 함수를 식별한다(자세한 내용은
`tests/modules/render/fixtures/README.md` 참고).
"""
import json
from pathlib import Path

import jsonschema
import pytest

from modules.render.escape import escape_html
from modules.render.url_sanitizer import sanitize_url
from modules.render.css_sanitizer import sanitize_css_value
from modules.render.heading import generate_heading_id, render_heading
from modules.render.bold_italic_strike import render_bold

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "modules" / "render" / "fixtures"
MANIFEST_PATH = REPO_ROOT / "src" / "modules" / "render" / "manifest.json"
SCHEMA_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "schema" / "cross_language_fixture.schema.json"
)

FIXTURE_FILES = sorted(FIXTURES_DIR.glob("*.json"))


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _function_name(fixture_path: Path) -> str:
    """fixture 파일명의 `__` 앞부분에서 대상 함수명을 추출한다."""
    return fixture_path.stem.split("__", 1)[0]


def _assert_escape_html(data):
    assert escape_html(data["input"]["text"]) == data["expected"]["html"]


def _assert_sanitize_url(data):
    assert sanitize_url(data["input"]["url"]) == data["expected"]["url"]


def _assert_sanitize_css_value(data):
    assert sanitize_css_value(data["input"]["value"]) == data["expected"]["value"]


def _assert_generate_heading_id(data):
    assert generate_heading_id(data["input"]["text"]) == data["expected"]["id"]


def _assert_render_bold(data):
    assert render_bold(data["input"]["text"]) == data["expected"]["html"]


def _assert_render_heading(data):
    result = render_heading(data["input"]["level"], data["input"]["content"])
    assert result == data["expected"]["html"]


ASSERTIONS = {
    "escape_html": _assert_escape_html,
    "sanitize_url": _assert_sanitize_url,
    "sanitize_css_value": _assert_sanitize_css_value,
    "generate_heading_id": _assert_generate_heading_id,
    "render_bold": _assert_render_bold,
    "render_heading": _assert_render_heading,
}


def test_fixtures_directory_matches_manifest():
    """manifest.json 의 fixtures.path/format 이 실제 디렉터리와 일치한다."""
    manifest = _load_json(MANIFEST_PATH)
    assert manifest["fixtures"]["path"] == "tests/modules/render/fixtures"
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
def test_fixture_function_name_is_known(fixture_path):
    """fixture 파일명이 가리키는 함수가 ASSERTIONS 디스패치 테이블에 존재한다."""
    assert _function_name(fixture_path) in ASSERTIONS


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=lambda p: p.stem)
def test_render_function_matches_fixture(fixture_path):
    """render 함수의 실제 동작이 fixture 의 expected/errors 와 일치한다."""
    data = _load_json(fixture_path)

    assert data["errors"] == []
    ASSERTIONS[_function_name(fixture_path)](data)
