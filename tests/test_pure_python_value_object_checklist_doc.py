"""`docs/pure-python-value-object-checklist.md` 가 태스크 0381 의 Notes
요구사항("dataclass/default/typing 사용 제한을 명시한다")을 실제로
고정하고 있으며, 그 제한이 현재 `src/modules/*/model.py` 의 실제
value object 코드와 어긋나지 않는지 확인한다.
"""
import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "pure-python-value-object-checklist.md"
MODEL_FILES = sorted((REPO_ROOT / "src" / "modules").glob("*/model.py"))

REQUIRED_DOC_HEADINGS = [
    "## 체크리스트",
    "### 1. dataclass 사용 제한",
    "### 2. 기본값(default) 제한",
    "### 3. typing 사용 제한",
    "## PHP 대응 표",
    "## 적용 대상",
]

ALLOWED_TYPING_NAMES = {"Optional", "List", "Dict", "Any", "Literal"}
FORBIDDEN_TYPING_NAMES = {
    "Union",
    "Generic",
    "TypeVar",
    "Protocol",
    "TypedDict",
    "NewType",
    "Callable",
}


def test_pure_python_value_object_checklist_doc_exists():
    """value object 체크리스트 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_pure_python_value_object_checklist_doc_has_required_sections():
    """dataclass/default/typing 세 제한 절과 PHP 대응 표, 적용 대상 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_pure_python_value_object_checklist_doc_references_related_docs():
    """이식성 계층 규칙과 기존 전략/이름 규칙 문서에 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "AGENTS.md" in content
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/dto-naming-convention.md" in content
    assert "docs/php-namespace-mapping.md" in content
    assert "docs/portability-glossary.md" in content


def test_pure_python_value_object_checklist_doc_cites_existing_examples():
    """문서가 드는 예시 클래스가 실제 model.py 에 존재하는 이름과 일치한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for example in [
        "Document",
        "Revision",
        "User",
        "RenderMetadata",
        "ParserDiagnostic",
    ]:
        assert example in content, f"missing example class name: {example}"


def _model_file_exists():
    assert MODEL_FILES, "no model.py files found under src/modules to validate against the doc"


def test_existing_model_files_do_not_use_dataclass():
    """현재 model.py 어디에도 @dataclass 데코레이터가 없다 — 체크리스트 1항."""
    _model_file_exists()
    for path in MODEL_FILES:
        content = path.read_text(encoding="utf-8")
        assert "dataclass" not in content, f"{path} uses dataclass, violating the checklist"


def test_existing_model_files_only_use_none_or_literal_defaults():
    """생성자 기본값이 None 또는 불변 리터럴만 쓰인다 — 체크리스트 2항."""
    _model_file_exists()
    for path in MODEL_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or node.name != "__init__":
                continue
            for default in node.args.defaults:
                assert isinstance(default, (ast.Constant,)), (
                    f"{path}::__init__ has a non-literal default "
                    f"({ast.dump(default)}), violating the checklist"
                )
                if isinstance(default.value, (list, dict)):
                    raise AssertionError(
                        f"{path}::__init__ uses a mutable literal default, "
                        "violating the checklist"
                    )


def test_existing_model_files_only_import_allowed_typing_names():
    """model.py 의 typing import 가 Optional/List/Dict/Any/Literal 로 한정된다 — 체크리스트 3항."""
    _model_file_exists()
    for path in MODEL_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                imported = {alias.name for alias in node.names}
                forbidden = imported & FORBIDDEN_TYPING_NAMES
                assert not forbidden, f"{path} imports forbidden typing names: {forbidden}"
                unknown = imported - ALLOWED_TYPING_NAMES
                assert not unknown, f"{path} imports typing names outside the checklist: {unknown}"


def test_pure_python_value_object_checklist_doc_lists_forbidden_typing_names():
    """금지된 typing 이름이 문서에 실제로 나열되어 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for name in sorted(FORBIDDEN_TYPING_NAMES):
        assert name in content, f"missing forbidden typing name in doc: {name}"
