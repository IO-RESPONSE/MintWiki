"""`docs/portable-text-normalization-policy.md` 가 태스크 0386 의 Notes
요구사항("Unicode normalization과 case 정책을 명시한다")을 실제로
고정하고 있으며, 그 정책이 현재 `normalize_title`/렌더러/검색 어댑터의
실제 관행 및 `docs/persistence-boundaries.md` 의 컬럼 정의와 어긋나지
않는지 확인한다.
"""
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "portable-text-normalization-policy.md"
PERSISTENCE_DOC_PATH = REPO_ROOT / "docs" / "persistence-boundaries.md"
TITLE_MODULE_PATH = REPO_ROOT / "src" / "modules" / "document" / "title.py"
HEADING_MODULE_PATH = REPO_ROOT / "src" / "modules" / "render" / "heading.py"

REQUIRED_DOC_HEADINGS = [
    "## 공백 정규화: 트림 + 내부 공백 단일 공백 축소",
    "## Unicode 정규화 폼: NFC",
    "## Case 정책: 저장/식별용은 보존, 비교/매칭용은 폴딩",
    "## DB collation: normalized_title UNIQUE는 대소문자를 구분해야 한다",
    "## 이 문서가 하지 않는 것",
]


def test_portable_text_normalization_policy_doc_exists():
    """텍스트 정규화 정책 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_portable_text_normalization_policy_doc_has_required_sections():
    """공백, Unicode 정규화, case, collation, 범위 제외 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_portable_text_normalization_policy_doc_fixes_unicode_normalization_form():
    """Unicode 정규화 폼(NFC)과 Python/PHP 양쪽 구현 방법을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "NFC" in content
    assert 'unicodedata.normalize("NFC"' in content
    assert "Normalizer::normalize" in content
    assert "FORM_C" in content


def test_portable_text_normalization_policy_doc_distinguishes_case_folding_purposes():
    """식별용(보존)과 비교용(폴딩) case 정책을 구분해서 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "casefold()" in content
    assert "mb_strtolower" in content
    assert "strtolower()" in content


def test_portable_text_normalization_policy_doc_addresses_collation_difference():
    """PostgreSQL과 MariaDB의 기본 collation 대소문자 구분 차이를 다룬다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "PostgreSQL" in content
    assert "MariaDB" in content
    assert "utf8mb4_bin" in content
    assert "_ci" in content


def test_portable_text_normalization_policy_doc_references_related_docs():
    """기존 전략/id/정렬/영속성/검색/용어 문서와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/portable-id-policy.md" in content
    assert "docs/portable-sorting-contract.md" in content
    assert "docs/persistence-boundaries.md" in content
    assert "docs/search-adapter-design.md" in content
    assert "docs/portability-glossary.md" in content


def test_normalized_title_column_is_documented_unique_not_null():
    """이 정책이 대소문자 구분을 요구하는 normalized_title 컬럼이 실제로
    NOT NULL/UNIQUE 로 고정돼 있는지 persistence-boundaries.md 의 컬럼
    정의를 통해 확인한다."""
    content = PERSISTENCE_DOC_PATH.read_text(encoding="utf-8")
    assert "| `normalized_title` | String(500) | NOT NULL, UNIQUE |" in content


def test_existing_normalize_title_does_not_case_fold():
    """현재 normalize_title 구현이 대소문자를 보존한다는 문서의 전제(저장·
    식별용 정규화는 case-folding 을 하지 않는다)가 실제 코드와 맞는지
    확인한다."""
    file_text = TITLE_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(file_text)
    sources = [
        ast.get_source_segment(file_text, node)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "normalize_title"
    ]
    assert sources, "normalize_title not found in document/title.py"
    assert any(
        source is not None and "lower" not in source and "casefold" not in source
        for source in sources
    ), "normalize_title unexpectedly case-folds its input"


def test_existing_heading_slug_uses_ascii_lower_not_casefold():
    """문서가 명시한 예외(heading 슬러그 생성은 ASCII 전용 lower() 를 그대로
    유지한다)가 실제 코드와 맞는지 확인한다."""
    file_text = HEADING_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(file_text)
    sources = [
        ast.get_source_segment(file_text, node)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "generate_heading_id"
    ]
    assert sources, "generate_heading_id not found in render/heading.py"
    assert any(
        source is not None and "text.lower()" in source
        for source in sources
    ), "generate_heading_id no longer uses str.lower() for slug generation"
