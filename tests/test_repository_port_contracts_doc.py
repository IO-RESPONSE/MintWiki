"""`docs/repository-port-contracts.md` 가 태스크 0378 의 Notes 요구사항
("ORM 의존 없는 인터페이스 기준으로 적는다")을 실제로 지키고 있으며, 문서가
나열한 메서드가 각 모듈 `repository.py` 의 `@abstractmethod` 목록과
어긋나지 않는지 확인한다.
"""
import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "repository-port-contracts.md"
MODULES_DIR = REPO_ROOT / "src" / "modules"

REQUIRED_DOC_HEADINGS = [
    "## document (",
    "## revision (",
    "## discussion (",
    "## user (",
    "## user 차단 (",
    "## user 세션 (",
    "## 공통 패턴",
]

REPOSITORY_FILES = {
    "document": ("repository.py", "DocumentRepository"),
    "revision": ("repository.py", "RevisionRepository"),
    "discussion": ("repository.py", "DiscussionRepository"),
    "user": ("repository.py", "UserRepository"),
    "user_block": ("block_repository.py", "BlockRepository"),
    "user_session": ("session_repository.py", "SessionRepository"),
}

ORM_LEAK_PATTERNS = ["ORM", "AsyncSession", "sqlalchemy"]


def _abstract_method_names(module_name, file_name, class_name):
    module_dir = "user" if module_name.startswith("user") else module_name
    source = (MODULES_DIR / module_dir / file_name).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    is_abstract = any(
                        (isinstance(d, ast.Name) and d.id == "abstractmethod")
                        or (isinstance(d, ast.Attribute) and d.attr == "abstractmethod")
                        for d in item.decorator_list
                    )
                    if is_abstract:
                        names.append(item.name)
    return names


def test_repository_port_contracts_doc_exists():
    """저장소 포트 계약 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_repository_port_contracts_doc_has_section_per_repository():
    """문서화 대상 저장소 포트마다 하나의 섹션을 갖는다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_repository_port_contracts_doc_lists_all_abstract_methods():
    """문서가 각 저장소 ABC 의 실제 `@abstractmethod` 이름을 빠짐없이 담는다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for module_name, (file_name, class_name) in REPOSITORY_FILES.items():
        method_names = _abstract_method_names(module_name, file_name, class_name)
        assert method_names, f"no abstractmethod found for {class_name}"
        for method_name in method_names:
            assert f"`{method_name}`" in content, (
                f"{class_name}.{method_name} not documented in {DOC_PATH.name}"
            )


def test_repository_port_contracts_doc_is_orm_independent():
    """문서 본문(코드 예시 제외 취지)의 시그니처가 ORM 타입을 노출하지 않는다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    table_rows = [line for line in content.splitlines() if line.startswith("| `")]
    assert table_rows, "no contract table rows found to validate"
    for row in table_rows:
        for pattern in ORM_LEAK_PATTERNS:
            assert pattern not in row, f"ORM-dependent type leaked into contract row: {row}"


def test_repository_port_contracts_doc_scopes_out_unimplemented_admin_module():
    """아직 repository.py 가 없는 admin 모듈은 문서에 새 섹션으로 실리지 않는다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    module_name = "admin"
    assert not (MODULES_DIR / module_name / "repository.py").exists(), (
        f"{module_name}/repository.py now exists — update the doc with a real "
        "contract section instead of leaving it scoped out"
    )
    assert re.search(r"^## admin", content, re.MULTILINE) is None


def test_repository_port_contracts_doc_references_related_docs():
    """전략/서비스 계약/exception-code/persistence/용어집 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/service-method-contracts.md" in content
    assert "docs/portable-exception-code-policy.md" in content
    assert "docs/persistence-boundaries.md" in content
    assert "docs/portability-glossary.md" in content
