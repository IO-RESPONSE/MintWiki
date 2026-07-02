"""`docs/php-parity-test-plan.md` 가 태스크 0387 의 목표("PHP parity 테스트
계획을 문서화한다")와 Notes 요구사항("같은 fixture 를 양쪽 런타임에서
실행하는 방식을 적는다")을 실제로 고정하고 있으며, 그 계획이 이미
존재하는 Python fixture 러너의 실제 관행과 어긋나지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-parity-test-plan.md"
TITLE_FIXTURES_TEST_PATH = (
    REPO_ROOT / "tests" / "modules" / "document" / "test_title_fixtures.py"
)
DECISION_CODE_FIXTURES_TEST_PATH = (
    REPO_ROOT / "tests" / "modules" / "acl" / "test_decision_code_fixtures.py"
)

REQUIRED_DOC_HEADINGS = [
    "## 핵심 원칙: 같은 fixture 파일을 두 런타임이 그대로 공유한다",
    "## Python 쪽 실행 방식 (이미 존재)",
    "## PHP 쪽 실행 방식 (계획, 0406/0407/0425 이후 구현)",
    "## Parity 판정 기준",
    "## 실행 방법 (계획)",
    "## 이 문서가 하지 않는 것",
]


def test_php_parity_test_plan_doc_exists():
    """PHP parity 테스트 계획 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_parity_test_plan_doc_has_required_sections():
    """공유 원칙, Python/PHP 실행 방식, 판정 기준, 실행 방법, 범위 제외
    절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_parity_test_plan_doc_fixes_shared_fixture_execution():
    """같은 fixture 파일을 두 런타임이 복사 없이 그대로 공유한다는 방식을
    명시한다(태스크 Notes 요구사항)."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "tests/modules/<module>/fixtures/" in content
    assert "tests/fixtures/" in content
    assert "복사" in content


def test_php_parity_test_plan_doc_defines_pass_criteria_using_error_codes():
    """parity 판정이 반환값뿐 아니라 error code 일치까지 요구한다는 것을
    명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "error code" in content
    assert "<module>.<reason>" in content
    assert "docs/portable-exception-code-policy.md" in content


def test_php_parity_test_plan_doc_addresses_not_yet_ported_modules():
    """아직 PHP 로 포팅되지 않은 모듈을 parity 실패로 집계하지 않는다는
    placeholder 정책을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "port.status" in content
    assert "skip" in content


def test_php_parity_test_plan_doc_references_related_docs():
    """전략/용어/fixture 위치/스키마/error code/namespace/manifest 문서와
    연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-replacement-strategy.md",
        "docs/portability-glossary.md",
        "docs/fixture-directory-convention.md",
        "docs/cross-language-fixture-schema.md",
        "docs/portable-exception-code-policy.md",
        "docs/php-namespace-mapping.md",
        "docs/module-contract-manifest-schema.md",
        "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"


def test_php_parity_test_plan_doc_does_not_claim_php_runner_is_implemented():
    """이 태스크가 PHP 러너 코드를 실제로 만들지 않는다는 범위 제외를
    명시한다(Out of Scope: 이후 태스크 0406/0407/0425-0429 의 범위)."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "php/" in content
    assert "0406" in content
    assert "0425" in content


def test_existing_python_fixture_runners_already_follow_the_planned_pattern():
    """이 문서가 "이미 존재" 한다고 서술하는 Python 쪽 fixture 러너
    패턴(schema 검증 -> 공개 메서드 실행 -> expected/errors 비교)이 실제
    코드에도 있는지 확인한다."""
    for path in (TITLE_FIXTURES_TEST_PATH, DECISION_CODE_FIXTURES_TEST_PATH):
        source = path.read_text(encoding="utf-8")
        assert "cross_language_fixture.schema.json" in source
        assert "jsonschema.validate" in source
        assert "fixtures.path" in source or 'manifest["fixtures"]' in source
