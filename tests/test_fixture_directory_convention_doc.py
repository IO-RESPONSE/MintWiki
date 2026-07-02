"""`docs/fixture-directory-convention.md` 가 태스크 0368 의 Notes 요구사항
(JSON fixture를 기본으로 하는 교차언어 fixture 디렉터리 규칙 고정)을
유지하는지, 그리고 실제 `tests/fixtures/` 디렉터리가 이 규칙대로 존재하는지
확인한다.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "fixture-directory-convention.md"
SHARED_FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
MODULES_DIR = REPO_ROOT / "src" / "modules"

REQUIRED_HEADINGS = [
    "## 두 종류의 fixture 디렉터리",
    "### 1. 모듈 전용 fixture",
    "### 2. 공유 fixture",
    "## 형식: JSON 기본",
    "## 파일 이름 규칙",
]


def test_fixture_directory_convention_doc_exists():
    """fixture 디렉터리 규칙 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_fixture_directory_convention_doc_has_required_sections():
    """모듈 전용/공유 fixture 구분과 JSON 기본 형식 정책이 모두 문서화되어 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_fixture_directory_convention_doc_references_related_docs():
    """기존 glossary/manifest 스키마 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/portability-glossary.md" in content
    assert "docs/module-contract-manifest-schema.md" in content


def test_shared_fixtures_directory_exists():
    """규칙이 가리키는 공유 fixture 디렉터리(tests/fixtures)가 실제로 존재한다."""
    assert SHARED_FIXTURES_DIR.is_dir()


def test_shared_fixtures_directory_does_not_overlap_module_fixture_paths():
    """공유 fixture 디렉터리는 어떤 모듈의 manifest fixtures.path 값과도 겹치지 않는다."""
    for manifest_path in sorted(MODULES_DIR.glob("*/manifest.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        module_fixtures_path = REPO_ROOT / data["fixtures"]["path"]
        assert module_fixtures_path != SHARED_FIXTURES_DIR, (
            f"module fixtures path collides with shared fixtures dir: {manifest_path}"
        )
        assert data["fixtures"]["format"] == "json"
