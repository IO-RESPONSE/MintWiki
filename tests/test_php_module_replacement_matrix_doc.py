"""`docs/php-module-replacement-matrix.md` 가 태스크 0433 의 목표(모듈별
Python/PHP 구현 상태 matrix)와 Notes 요구사항(not-started/partial/parity/
pass 상태를 둔다)을 실제로 고정하고 있으며, 그 표가 저장소에 실제로
존재하는 모듈 목록·PHP 코드 존재 여부와 어긋나지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-module-replacement-matrix.md"
MODULES_ROOT = REPO_ROOT / "src" / "modules"
PHP_MODULES_ROOT = REPO_ROOT / "php" / "src" / "Modules"

REQUIRED_HEADINGS = [
    "## 상태 정의 (4단계)",
    "## 모듈별 matrix",
    "## 이 표를 최신으로 유지하는 방법",
    "## 이 문서가 하지 않는 것",
]

STATUS_LABELS = ["not-started", "partial", "parity", "pass"]


def _module_names():
    return sorted(
        path.name
        for path in MODULES_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith("__")
    )


def _php_module_dir_name(module_name):
    return module_name[:1].upper() + module_name[1:]


def _php_module_has_domain_code(module_name):
    """`README.md` 를 제외한 실제 PHP 클래스 파일이 있는지 확인한다."""
    php_dir = PHP_MODULES_ROOT / _php_module_dir_name(module_name)
    if not php_dir.is_dir():
        return False
    return any(
        path.is_file() and path.name != "README.md"
        for path in php_dir.iterdir()
    )


def test_php_module_replacement_matrix_doc_exists():
    """모듈 교체 matrix 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_module_replacement_matrix_doc_has_required_sections():
    """상태 정의, matrix 표, 갱신 방법, 범위 제외 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_module_replacement_matrix_doc_defines_all_four_statuses():
    """Notes 가 요구한 not-started/partial/parity/pass 4개 상태를 모두
    정의한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for label in STATUS_LABELS:
        assert f"**{label}**" in content, f"missing status definition: {label}"


def test_php_module_replacement_matrix_doc_covers_every_existing_module():
    """저장소에 실제로 존재하는 모든 모듈이 matrix 표에 등장한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for name in _module_names():
        assert f"| {name} |" in content, f"module missing from matrix table: {name}"


def test_php_module_replacement_matrix_doc_uses_only_defined_statuses():
    """matrix 표의 PHP 구현 상태 열은 정의된 4개 상태값만 사용한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    table_section = content.split("## 모듈별 matrix")[1].split("\n## ")[0]
    module_names = set(_module_names())
    for line in table_section.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0] not in module_names:
            continue
        php_status = cells[2]
        assert php_status in STATUS_LABELS, (
            f"unexpected status value for {cells[0]}: {php_status}"
        )


def test_php_module_replacement_matrix_doc_matches_actual_php_domain_code():
    """PHP 도메인 코드 존재 여부와 matrix 표의 상태가 어긋나지 않는다 —
    도메인 클래스가 없는 모듈은 not-started 로, 있는 모듈은 partial 이상
    으로 표시해야 한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    table_section = content.split("## 모듈별 matrix")[1].split("\n## ")[0]
    rows = {}
    for line in table_section.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0] not in _module_names():
            continue
        rows[cells[0]] = cells[2]

    for name in _module_names():
        assert name in rows, f"module missing from matrix table: {name}"
        has_code = _php_module_has_domain_code(name)
        status = rows[name]
        if has_code:
            assert status != "not-started", (
                f"{name} has PHP domain code but is marked not-started"
            )
        else:
            assert status == "not-started", (
                f"{name} has no PHP domain code but is marked {status}"
            )


def test_php_module_replacement_matrix_doc_references_related_docs():
    """전략/체크리스트/parity 계획/manifest 스키마/모듈 목록 문서와
    연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-replacement-strategy.md",
        "docs/php-replacement-readiness-checklist.md",
        "docs/php-parity-test-plan.md",
        "docs/module-contract-manifest-schema.md",
        "docs/modules.md",
        "docs/php-namespace-mapping.md",
        "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
