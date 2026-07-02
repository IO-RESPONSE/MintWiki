"""`docs/portable-sorting-contract.md` 가 태스크 0385 의 Notes 요구사항
("DB별 NULL 정렬 차이를 피한다")을 실제로 고정하고 있으며, 그 정책이
현재 revision/discussion 모듈의 실제 정렬 관행 및
`docs/persistence-boundaries.md` 의 컬럼 정의와 어긋나지 않는지 확인한다.
"""
import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "portable-sorting-contract.md"
PERSISTENCE_DOC_PATH = REPO_ROOT / "docs" / "persistence-boundaries.md"
REVISION_REPOSITORY_PATH = REPO_ROOT / "src" / "modules" / "revision" / "repository.py"

REQUIRED_DOC_HEADINGS = [
    "## 기본 정렬 키: `created_at` 오름차순(생성 순서)",
    "## Tie-breaking: `id` 를 보조 정렬 키로 쓴다",
    "## NULL 정렬: PostgreSQL과 MariaDB 기본값 차이를 피한다",
    "## 이 문서가 하지 않는 것",
]


def test_portable_sorting_contract_doc_exists():
    """정렬 계약 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_portable_sorting_contract_doc_has_required_sections():
    """기본 정렬 키, tiebreak, NULL 정렬, 범위 제외 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_portable_sorting_contract_doc_fixes_default_sort_key_and_tiebreak():
    """기본 정렬 키(created_at)와 동률 처리 키(id)를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "created_at" in content
    assert "생성 순서" in content
    assert "ORDER BY created_at, id" in content


def test_portable_sorting_contract_doc_addresses_null_ordering_difference():
    """PostgreSQL과 MariaDB의 NULL 정렬 기본값 차이를 명시적으로 다룬다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "PostgreSQL" in content
    assert "MariaDB" in content
    assert "NULLS LAST" in content
    assert "NULLS FIRST" in content
    assert "COALESCE" in content


def test_portable_sorting_contract_doc_references_related_docs():
    """기존 전략/페이지네이션/영속성/datetime/id/용어 문서와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/portable-pagination-contract.md" in content
    assert "docs/persistence-boundaries.md" in content
    assert "docs/portable-datetime-policy.md" in content
    assert "docs/portable-id-policy.md" in content
    assert "docs/portability-glossary.md" in content


def test_default_sort_key_columns_are_documented_not_null():
    """계약이 고정한 기본 정렬 키(id, created_at)가 실제로 NOT NULL/PRIMARY KEY 로
    고정돼 있는지 persistence-boundaries.md 의 컬럼 정의를 통해 확인한다.
    NULL 정렬 차이가 나타나지 않는다는 이 계약의 전제가 실제 스키마와
    맞아야 한다."""
    content = PERSISTENCE_DOC_PATH.read_text(encoding="utf-8")
    id_rows = re.findall(r"^\| `id` \|.*\|$", content, flags=re.MULTILINE)
    created_at_rows = re.findall(r"^\| `created_at` \|.*\|$", content, flags=re.MULTILINE)
    assert id_rows, "no `id` column definitions found in persistence-boundaries.md"
    assert created_at_rows, "no `created_at` column definitions found in persistence-boundaries.md"
    for row in id_rows:
        assert "PRIMARY KEY" in row, f"id column not documented as PRIMARY KEY: {row}"
    for row in created_at_rows:
        assert "NOT NULL" in row, f"created_at column not documented as NOT NULL: {row}"


def test_existing_revision_list_method_sorts_by_created_at():
    """revision 저장소의 실제 list_by_document_id 구현이 문서가 고정한 기본
    정렬 키(created_at)를 실제로 쓰고 있는지 확인한다."""
    file_text = REVISION_REPOSITORY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(file_text)
    sources = [
        ast.get_source_segment(file_text, node)
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "list_by_document_id"
    ]
    assert sources, "list_by_document_id not found in revision/repository.py"
    assert any(
        source is not None and "order_by" in source and "created_at" in source
        for source in sources
    ), "no list_by_document_id implementation sorts by created_at via order_by"
