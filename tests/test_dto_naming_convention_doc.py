"""`docs/dto-naming-convention.md` 가 태스크 0376 의 Notes 요구사항
("Request/Response/ReadModel 구분을 고정한다")을 실제로 고정하고 있으며,
그 규칙이 현재 저장소의 `schema.py`/`service.py` DTO 이름과 어긋나지
않는지 확인한다.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "dto-naming-convention.md"

REQUIRED_DOC_HEADINGS = [
    "## 세 가지 DTO 역할",
    "### Request",
    "### Response",
    "### ReadModel",
    "## 어디에 선언하는가",
    "## PHP 대응 규칙",
    "## 금지 사항",
]

REQUEST_CLASS_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*Request$")
RESPONSE_CLASS_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*Response$")
READ_MODEL_CLASS_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*ReadModel$")


def test_dto_naming_convention_doc_exists():
    """DTO 네이밍 규칙 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_dto_naming_convention_doc_has_required_sections():
    """Request/Response/ReadModel 역할 구분, 선언 위치, PHP 대응, 금지 사항 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_dto_naming_convention_doc_cites_existing_examples():
    """문서가 드는 예시 클래스가 실제 schema.py/service.py 에 존재하는 이름과 일치한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for example in [
        "CreateDocumentRequest",
        "DocumentResponse",
        "CreateThreadRequest",
        "ThreadResponse",
        "ListThreadsResponse",
        "RevisionResponse",
        "CurrentRevisionReadModel",
    ]:
        assert example in content, f"missing example class name: {example}"


def test_dto_naming_convention_doc_references_related_docs():
    """기존 전략/이식성 용어/네임스페이스/manifest 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/portability-glossary.md" in content
    assert "docs/php-namespace-mapping.md" in content
    assert "docs/module-contract-manifest-schema.md" in content


def _collect_schema_dto_class_names():
    """모든 모듈 schema.py 에 정의된 최상위 DTO 클래스 이름을 모은다."""
    names = []
    for schema_path in sorted((REPO_ROOT / "src" / "modules").glob("*/schema.py")):
        content = schema_path.read_text(encoding="utf-8")
        names.extend(re.findall(r"^class (\w+)\(BaseModel\):", content, re.MULTILINE))
    return names


def test_existing_schema_dto_names_only_use_request_or_response_suffix():
    """schema.py 의 DTO 는 모두 Request 또는 Response 로 끝나며, 문서가 금지한 다른 suffix를 쓰지 않는다."""
    names = _collect_schema_dto_class_names()
    assert names, "no schema.py DTO classes found to validate against the doc"
    for name in names:
        assert REQUEST_CLASS_PATTERN.match(name) or RESPONSE_CLASS_PATTERN.match(name), (
            f"schema.py DTO class does not follow Request/Response naming: {name}"
        )


def test_existing_read_model_names_follow_read_model_suffix():
    """service.py 등에 선언된 ReadModel 클래스가 문서가 고정한 `<Noun>ReadModel` 형식을 따른다."""
    found = []
    for py_path in (REPO_ROOT / "src" / "modules").rglob("*.py"):
        if py_path.name == "schema.py":
            continue
        content = py_path.read_text(encoding="utf-8")
        found.extend(re.findall(r"^class (\w*ReadModel)\b", content, re.MULTILINE))
    assert "CurrentRevisionReadModel" in found
    for name in found:
        assert READ_MODEL_CLASS_PATTERN.match(name), f"ReadModel class does not match naming: {name}"
