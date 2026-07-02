"""`docs/portable-id-policy.md` 가 태스크 0383 의 Notes 요구사항
("DB native UUID 대신 문자열 ID 기본을 고정한다")을 실제로 고정하고 있으며,
그 정책이 현재 서비스 계층 코드의 실제 `id` 생성 방식과 어긋나지 않는지
확인한다.
"""
import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "portable-id-policy.md"
MODULE_FILES = sorted((REPO_ROOT / "src" / "modules").glob("**/*.py"))

# 문서 서두에서 "이미 str(uuid.uuid4())로 id 를 생성하고 있다"고 명시한
# 파일들만 검증 대상으로 삼는다. `acl/default_policy.py` 같은 정적 정책
# 규칙 id(예: "default-public-read-allow")는 요청마다 새로 생성되는
# 엔티티 id 가 아니므로 이 정책의 대상이 아니다.
ENTITY_ID_GENERATION_FILES = [
    REPO_ROOT / "src" / "modules" / "document" / "service.py",
    REPO_ROOT / "src" / "modules" / "revision" / "service.py",
    REPO_ROOT / "src" / "modules" / "discussion" / "service.py",
    REPO_ROOT / "src" / "modules" / "acl" / "audit_recorder.py",
    REPO_ROOT / "src" / "modules" / "discussion" / "audit_recorder.py",
]

REQUIRED_DOC_HEADINGS = [
    "## 생성 정책: 애플리케이션 계층에서 생성",
    "## 형식: UUID v4, canonical 36자 소문자 문자열",
    "## 저장 정책: 문자열 컬럼",
    "## PHP 구현 규칙",
    "## 이 문서가 하지 않는 것",
]


def test_portable_id_policy_doc_exists():
    """ID 정책 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_portable_id_policy_doc_has_required_sections():
    """생성, 형식, 저장, PHP 규칙, 범위 제외 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_portable_id_policy_doc_fixes_application_generation_rule():
    """id 생성이 DB가 아니라 애플리케이션 계층 책임임을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "DB가 생성하지 않는다" in content
    assert "AUTO_INCREMENT" in content
    assert "gen_random_uuid()" in content


def test_portable_id_policy_doc_fixes_string_storage_rule():
    """String(255) 문자열 컬럼 저장과 native UUID 컬럼 회피를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "String(255)" in content
    assert "native" in content.lower()


def test_portable_id_policy_doc_references_related_docs():
    """기존 전략/영속/계약/datetime 정책 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/persistence-boundaries.md" in content
    assert "docs/service-method-contracts.md" in content
    assert "docs/repository-port-contracts.md" in content
    assert "docs/portable-datetime-policy.md" in content
    assert "docs/portability-glossary.md" in content


def _module_uuid_id_assignments():
    """엔티티 id 를 생성하는 파일들에서 `id=...` 키워드 인자로 넘겨지는 값의 AST 노드를 모은다."""
    assignments = []
    for path in ENTITY_ID_GENERATION_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "id":
                        assignments.append((path, kw.value))
    return assignments


def test_existing_service_layer_only_generates_id_via_uuid4_str():
    """실제 코드가 문서의 정책대로 `str(uuid.uuid4())` 로만 id 를 생성한다."""
    assignments = _module_uuid_id_assignments()
    assert assignments, "no id=... keyword assignments found under src/modules to validate against the doc"
    for path, value in assignments:
        is_str_uuid4_call = (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "str"
            and len(value.args) == 1
            and isinstance(value.args[0], ast.Call)
            and isinstance(value.args[0].func, ast.Attribute)
            and value.args[0].func.attr == "uuid4"
        )
        assert is_str_uuid4_call, (
            f"{path}: id= keyword argument is not str(uuid.uuid4()), "
            "violating the application-layer UUID v4 generation policy"
        )


def test_existing_module_files_never_use_db_native_id_generation():
    """DB native id 생성 함수(SERIAL/AUTO_INCREMENT/gen_random_uuid 등)를 쓰지 않는다."""
    forbidden_patterns = ["AUTO_INCREMENT", "SERIAL", "gen_random_uuid(", "autoincrement=True"]
    for path in MODULE_FILES:
        content = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert pattern not in content, (
                f"{path} uses {pattern!r}, violating the application-layer id generation policy"
            )


def test_documented_uuid_example_is_canonical_v4_format():
    """문서의 예시 UUID 문자열이 canonical 36자 소문자 v4 형식과 일치한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    match = re.search(r"예: `([0-9a-f-]{36})`", content)
    assert match, "doc must contain a canonical UUID example wrapped in backticks"
    example = match.group(1)
    canonical_v4_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    )
    assert canonical_v4_pattern.match(example), f"{example} is not a canonical UUID v4 string"
