"""`docs/portable-exception-code-policy.md` 가 태스크 0373 의 Notes
요구사항("PHP와 Python이 같은 code를 반환하게 한다")과
`docs/cross-language-fixture-schema.md` 의 `errors` 필드가 요구하는
안정적인 error code 형식을 실제로 고정하고 있는지 확인한다.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "portable-exception-code-policy.md"

REQUIRED_DOC_HEADINGS = [
    "## 왜 메시지 대신 code 인가",
    "## Code 형식",
    "## Code 는 어디에 선언하는가",
    "## Code 소유권과 유일성",
    "## 안정성(하위 호환)",
    "## fixture 와의 연결",
]

# docs/cross-language-fixture-schema.md 예시와 동일한 형식의 code.
CODE_FORMAT_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


def test_portable_exception_code_policy_doc_exists():
    """예외 코드 정책 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_portable_exception_code_policy_doc_has_required_sections():
    """메시지 금지 이유, code 형식, 선언 위치, 유일성, 안정성 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_portable_exception_code_policy_doc_fixes_example_codes():
    """fixture 스키마 문서와 같은 예시 code(document.empty_title 등)를 그대로 쓴다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "document.empty_title" in content
    assert "document.not_found" in content
    assert "document.duplicate_title" in content


def test_portable_exception_code_policy_doc_example_codes_match_format():
    """문서가 예시로 드는 code 문자열이 스스로 정의한 `<module>.<reason>` 형식을 만족한다."""
    example_codes = ["document.empty_title", "document.not_found", "document.duplicate_title"]
    for code in example_codes:
        assert CODE_FORMAT_PATTERN.match(code), f"example code does not match declared format: {code}"


def test_portable_exception_code_policy_doc_declares_python_code_attribute():
    """Python 예외가 code 를 노출하는 방식(클래스 속성 `code`)이 문서화되어 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "code = \"document.not_found\"" in content


def test_portable_exception_code_policy_doc_references_related_docs():
    """기존 전략/fixture/네임스페이스 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/cross-language-fixture-schema.md" in content
    assert "docs/module-contract-manifest-schema.md" in content
    assert "docs/portability-glossary.md" in content
    assert "docs/php-namespace-mapping.md" in content
