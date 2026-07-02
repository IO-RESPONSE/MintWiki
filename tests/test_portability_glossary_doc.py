"""`docs/portability-glossary.md` 필수 용어 정의가 유지되는지 확인한다.

이 문서는 태스크 0352 의 산출물이며, Notes 요구사항(port, adapter,
contract, fixture, shared hosting 용어 고정)이 이후 편집에서 실수로
삭제되지 않도록 제목 존재 여부를 회귀 테스트로 고정한다.
"""
from pathlib import Path

DOC_PATH = Path(__file__).resolve().parent.parent / "docs" / "portability-glossary.md"

REQUIRED_HEADINGS = [
    "## Port",
    "## Adapter",
    "## Contract",
    "## Fixture",
    "## Shared Hosting",
]


def test_portability_glossary_doc_exists():
    """용어집 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_portability_glossary_doc_has_required_terms():
    """Notes 에서 요구한 다섯 가지 용어가 모두 문서에 정의되어 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"missing required term heading: {heading}"


def test_portability_glossary_doc_references_replacement_strategy():
    """기존 전략 문서(docs/php-replacement-strategy.md)와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "AGENTS.md" in content
