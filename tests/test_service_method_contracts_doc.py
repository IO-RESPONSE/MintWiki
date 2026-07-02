"""`docs/service-method-contracts.md` 가 태스크 0377 의 Notes 요구사항
("모듈별 public method만 적는다")을 실제로 지키고 있으며, 문서가 나열한
메서드가 각 모듈 `manifest.json` 의 `service.public_methods` 와 어긋나지
않는지 확인한다.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "service-method-contracts.md"
MODULES_DIR = REPO_ROOT / "src" / "modules"

REQUIRED_DOC_HEADINGS = [
    "## document (",
    "## revision (",
    "## discussion (",
    "## acl (",
    "## user (",
    "## cache (",
    "## parser (",
    "## render (",
    "## search (",
    "## admin / audit / jobs (",
]


def _load_manifest_public_methods(module_name):
    manifest_path = MODULES_DIR / module_name / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest["service"]["public_methods"]


def test_service_method_contracts_doc_exists():
    """서비스 메서드 계약 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_service_method_contracts_doc_has_section_per_module():
    """구현 여부와 무관하게 모든 모듈에 대해 하나의 섹션을 갖는다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_service_method_contracts_doc_only_lists_manifest_public_methods():
    """문서가 각 모듈에 대해 적는 메서드 이름이 manifest 의 public_methods 와
    모순되지 않는다 — manifest 에 없는 이름을 새로 지어 넣지 않는다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    modules_with_declared_methods = [
        "acl",
        "admin",
        "audit",
        "cache",
        "discussion",
        "document",
        "jobs",
        "parser",
        "revision",
        "search",
        "user",
    ]
    for module_name in modules_with_declared_methods:
        for method_name in _load_manifest_public_methods(module_name):
            assert f"`{method_name}`" in content, (
                f"manifest public method not documented: {module_name}.{method_name}"
            )


def test_service_method_contracts_doc_documents_render_public_methods():
    """render 모듈은 클래스 기반 서비스가 아니므로 manifest 대신 __init__.py
    의 __all__ 공개 함수 목록과 대조한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    render_init = (MODULES_DIR / "render" / "__init__.py").read_text(encoding="utf-8")
    manifest = json.loads(
        (MODULES_DIR / "render" / "manifest.json").read_text(encoding="utf-8")
    )
    for method_name in manifest["service"]["public_methods"]:
        assert f'"{method_name}"' in render_init, (
            f"render manifest method not re-exported via __all__ in __init__.py: {method_name}"
        )
        assert f"`{method_name}`" in content, f"render manifest method not documented: {method_name}"


def test_service_method_contracts_doc_notes_unimplemented_modules():
    """아직 service.py 가 없는 모듈(admin/audit/jobs)은 구현 없음을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for module_name in ["admin", "audit", "jobs"]:
        assert not (MODULES_DIR / module_name / "service.py").exists(), (
            f"{module_name}/service.py now exists — update the doc's "
            "'아직 구현 없음' section instead of leaving it stale"
        )
    assert "아직 구현 없음" in content


def test_service_method_contracts_doc_references_related_docs():
    """전략/네이밍/manifest/exception-code/용어집 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/module-contract-manifest-schema.md" in content
    assert "docs/dto-naming-convention.md" in content
    assert "docs/portable-exception-code-policy.md" in content
    assert "docs/portability-glossary.md" in content
