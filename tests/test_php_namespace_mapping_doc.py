"""`docs/php-namespace-mapping.md` 가 태스크 0367 의 Notes 요구사항
(`modules.document.service` <-> `MintWiki\\Document\\Service` 식 고정)과
각 모듈 manifest 의 `port.target_namespace` 값을 그대로 반영하고 있는지
확인한다.

각 `src/modules/<module>/manifest.json` 은 이 문서가 나오기 전까지
target_namespace 를 "후보값"이라고 표시해 두었다(0353-0364 산출물). 이
회귀 테스트는 그 후보값이 이 문서의 매핑 표에서 실제로 확정 문서화되어
있는지, 그리고 모듈 하나가 실수로 누락되지 않는지를 고정한다.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-namespace-mapping.md"
MODULES_DIR = REPO_ROOT / "src" / "modules"


def _module_manifests():
    manifests = {}
    for manifest_path in sorted(MODULES_DIR.glob("*/manifest.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifests[data["module"]] = data
    return manifests


def test_php_namespace_mapping_doc_exists():
    """namespace 매핑 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_namespace_mapping_doc_covers_every_module_manifest():
    """모든 모듈 manifest 의 target_namespace 값이 매핑 표에 그대로 등장한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    manifests = _module_manifests()
    assert manifests, "module manifest 가 하나도 없으면 테스트 자체가 무의미하다"

    for module_name, manifest in manifests.items():
        target_namespace = manifest["port"]["target_namespace"]
        assert f"modules.{module_name}" in content, (
            f"missing python package reference for module: {module_name}"
        )
        assert target_namespace in content, (
            f"missing target namespace for module {module_name}: {target_namespace}"
        )


def test_php_namespace_mapping_doc_fixes_notes_example():
    """태스크 Notes 가 고정한 예시(document.service <-> MintWiki\\Document\\Service)가 남아 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "modules.document.service" in content
    assert "MintWiki\\Document\\Service" in content


def test_php_namespace_mapping_doc_references_related_docs():
    """기존 전략/스키마 문서와 모순 없이 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/module-contract-manifest-schema.md" in content
    assert "docs/modules.md" in content
