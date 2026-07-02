"""`docs/portable-pagination-contract.md` 가 태스크 0384 의 Notes 요구사항
("limit/offset 기본, cursor는 adapter 뒤로 둔다")을 실제로 고정하고 있으며,
그 정책이 현재 discussion 모듈의 실제 `list_*` 시그니처와 어긋나지 않는지
확인한다.
"""
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "portable-pagination-contract.md"

# 문서 서두에서 이미 limit/offset 을 쓰고 있다고 명시한 페이지네이션
# 대상 메서드들만 검증한다.
PAGINATED_METHOD_FILES = [
    REPO_ROOT / "src" / "modules" / "discussion" / "repository.py",
    REPO_ROOT / "src" / "modules" / "discussion" / "service.py",
]
PAGINATED_METHOD_NAMES = {
    "list_threads_by_document_id",
    "list_comments_by_thread_id",
}

REQUIRED_DOC_HEADINGS = [
    "## 기본 방식: limit/offset",
    "## Cursor 는 adapter 뒤로 둔다",
    "## 이 문서가 하지 않는 것",
]


def test_portable_pagination_contract_doc_exists():
    """페이지네이션 계약 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_portable_pagination_contract_doc_has_required_sections():
    """기본 방식, cursor 위치, 범위 제외 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_portable_pagination_contract_doc_fixes_limit_offset_defaults():
    """limit/offset 의 이름·타입·기본값을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "limit: Optional[int] = None" in content
    assert "offset: int = 0" in content


def test_portable_pagination_contract_doc_pushes_cursor_behind_adapter():
    """cursor 기반 페이지네이션이 공개 계약이 아니라 adapter 세부사항임을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "Cursor" in content
    assert "adapter" in content.lower()
    assert "노출하지 않는다" in content


def test_portable_pagination_contract_doc_references_related_docs():
    """기존 전략/계약/포트/용어 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/service-method-contracts.md" in content
    assert "docs/repository-port-contracts.md" in content
    assert "docs/portability-glossary.md" in content


def _paginated_method_defs():
    """검증 대상 파일에서 페이지네이션 대상 메서드의 함수 정의 AST 노드를 모은다."""
    defs = []
    for path in PAGINATED_METHOD_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.AsyncFunctionDef)
                and node.name in PAGINATED_METHOD_NAMES
            ):
                defs.append((path, node))
    return defs


def _arg_default_map(func_def):
    """함수 정의의 키워드 인자 이름과 기본값 AST 노드를 매핑한다."""
    args = func_def.args
    defaults = args.defaults
    named_args = args.args[len(args.args) - len(defaults):]
    return dict(zip((a.arg for a in named_args), defaults))


def test_existing_discussion_list_methods_use_limit_offset_defaults():
    """실제 코드가 문서의 정책대로 limit=None/offset=0 기본값을 쓴다."""
    defs = _paginated_method_defs()
    assert defs, "no paginated list_* methods found under discussion module to validate against the doc"
    for path, func_def in defs:
        default_map = _arg_default_map(func_def)
        assert "limit" in default_map, f"{path}:{func_def.name} missing limit parameter"
        assert "offset" in default_map, f"{path}:{func_def.name} missing offset parameter"

        limit_default = default_map["limit"]
        assert isinstance(limit_default, ast.Constant) and limit_default.value is None, (
            f"{path}:{func_def.name} limit default is not None, violating the pagination contract"
        )

        offset_default = default_map["offset"]
        assert isinstance(offset_default, ast.Constant) and offset_default.value == 0, (
            f"{path}:{func_def.name} offset default is not 0, violating the pagination contract"
        )


def test_existing_module_files_never_expose_cursor_pagination_parameters():
    """공개 서비스/저장소 메서드 시그니처에 cursor 파라미터를 노출하지 않는다."""
    module_files = sorted((REPO_ROOT / "src" / "modules").glob("**/*.py"))
    for path in module_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_names = {a.arg for a in node.args.args + node.args.kwonlyargs}
                forbidden = {"cursor", "page_token", "next_cursor"} & arg_names
                assert not forbidden, (
                    f"{path}:{node.name} exposes {forbidden} as a public parameter, "
                    "violating the 'cursor stays behind the adapter' pagination policy"
                )
