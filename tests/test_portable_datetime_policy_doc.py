"""`docs/portable-datetime-policy.md` 가 태스크 0382 의 Notes 요구사항
("UTC 저장, 표시 timezone 분리를 명시한다")을 실제로 고정하고 있으며, 그
정책이 현재 서비스/영속 계층 코드의 실제 `datetime` 사용과 어긋나지
않는지 확인한다.
"""
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "portable-datetime-policy.md"
MODULE_FILES = sorted((REPO_ROOT / "src" / "modules").glob("**/*.py"))

REQUIRED_DOC_HEADINGS = [
    "## 저장 정책: UTC 고정",
    "## 표시 정책: 저장과 표시의 분리",
    "## Wire 표현: ISO 8601 + UTC 오프셋",
    "## 이 문서가 하지 않는 것",
]


def test_portable_datetime_policy_doc_exists():
    """datetime 정책 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_portable_datetime_policy_doc_has_required_sections():
    """저장(UTC), 표시 분리, wire 표현, 범위 제외 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_portable_datetime_policy_doc_fixes_utc_storage_rule():
    """UTC 저장과 naive datetime 금지가 문서에 명시되어 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "datetime.now(timezone.utc)" in content
    assert "naive" in content
    assert "DateTime(timezone=True)" in content


def test_portable_datetime_policy_doc_fixes_display_separation_rule():
    """표시 timezone 변환이 도메인이 아니라 어댑터 계층 책임임을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "어댑터 계층" in content
    assert "표시 timezone" in content


def test_portable_datetime_policy_doc_references_related_docs():
    """기존 전략/영속/계약/fixture 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/persistence-boundaries.md" in content
    assert "docs/service-method-contracts.md" in content
    assert "docs/repository-port-contracts.md" in content
    assert "docs/cross-language-fixture-schema.md" in content
    assert "docs/portability-glossary.md" in content


def _module_datetime_now_calls():
    """src/modules 전체에서 `datetime.now(...)` 호출 AST 노드를 모은다."""
    calls = []
    for path in MODULE_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "now"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "datetime"
            ):
                calls.append((path, node))
    return calls


def test_existing_service_layer_only_uses_utc_aware_now():
    """실제 코드가 문서의 UTC 정책대로 `datetime.now(timezone.utc)` 만 쓴다."""
    calls = _module_datetime_now_calls()
    assert calls, "no datetime.now(...) calls found under src/modules to validate against the doc"
    for path, node in calls:
        assert len(node.args) == 1, (
            f"{path}:{node.lineno} calls datetime.now() without an explicit "
            "timezone argument, violating the UTC storage policy"
        )
        arg = node.args[0]
        is_timezone_utc = (
            isinstance(arg, ast.Attribute)
            and arg.attr == "utc"
            and isinstance(arg.value, ast.Name)
            and arg.value.id == "timezone"
        )
        assert is_timezone_utc, (
            f"{path}:{node.lineno} calls datetime.now() with a non-UTC "
            "timezone argument, violating the UTC storage policy"
        )


def test_existing_module_files_never_call_naive_utcnow():
    """deprecated 되고 naive 값을 반환하는 `datetime.utcnow()` 를 쓰지 않는다."""
    for path in MODULE_FILES:
        content = path.read_text(encoding="utf-8")
        assert "utcnow()" not in content, f"{path} calls datetime.utcnow(), violating the UTC storage policy"
