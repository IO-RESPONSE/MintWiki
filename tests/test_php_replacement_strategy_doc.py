"""`docs/php-replacement-strategy.md` 필수 절이 유지되는지 확인한다.

이 문서는 태스크 0351 의 산출물이며, Notes 요구사항(Python 유지 기간,
PHP 전환 기준, 금지할 결합)이 이후 편집에서 실수로 삭제되지 않도록
제목 존재 여부를 회귀 테스트로 고정한다.
"""
from pathlib import Path

DOC_PATH = Path(__file__).resolve().parent.parent / "docs" / "php-replacement-strategy.md"

REQUIRED_HEADINGS = [
    "## 전환 원칙: 모듈 단위 1:1 교체",
    "## Python 유지 기간",
    "## PHP 전환 기준 (모듈별 readiness gate)",
    "## 금지할 결합 (Forbidden Couplings)",
]


def test_php_replacement_strategy_doc_exists():
    """전략 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_replacement_strategy_doc_has_required_sections():
    """Notes 에서 요구한 세 가지 절이 모두 문서에 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_replacement_strategy_doc_references_boundary_check():
    """기존 이식성 경계 검사(scripts/check_boundaries.py)와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "scripts/check_boundaries.py" in content
    assert "AGENTS.md" in content
