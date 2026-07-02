"""`docs/portability-phase-qa-checklist.md` 가 태스크 0390 의 목표("Phase A
완료 QA 체크리스트를 추가한다")와 Notes 요구사항("manifest, fixtures,
boundary, docs 검증을 포함한다")을 실제로 고정하고 있으며, 체크리스트가
가리키는 스크립트/문서/테스트가 실제로 존재하고 서로 어긋나지 않는지
확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "portability-phase-qa-checklist.md"
QA_SCRIPT_PATH = REPO_ROOT / "scripts" / "qa.sh"

REQUIRED_DOC_HEADINGS = [
    "## 사용법",
    "## 1. Manifest 계약",
    "## 2. Fixture 계약",
    "## 3. Boundary(경계) 검사",
    "## 4. 문서(Docs) 정합성",
    "## 이 체크리스트가 다루지 않는 것",
    "## 관련 문서",
]

REFERENCED_SCRIPTS = [
    "scripts/check_module_manifests.py",
    "scripts/check_boundaries.py",
    "scripts/check_no_app_import_in_modules.py",
    "scripts/check_contract_drift.py",
]

REFERENCED_DOCS = [
    "docs/acl-phase-qa-checklist.md",
    "docs/php-replacement-strategy.md",
    "docs/module-contract-manifest-schema.md",
    "docs/fixture-directory-convention.md",
    "docs/cross-language-fixture-schema.md",
    "docs/php-replacement-readiness-checklist.md",
    "docs/php-parity-test-plan.md",
    "docs/contract-drift-report.md",
    "docs/php-db-ui-micro-job-prompts-0351-0670.md",
]


def test_portability_phase_qa_checklist_doc_exists():
    """Phase A QA 체크리스트 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_portability_phase_qa_checklist_doc_has_required_sections():
    """사용법, manifest/fixture/boundary/docs 4개 검증 절, 범위 제외,
    관련 문서 절이 모두 있다(Notes: manifest, fixtures, boundary, docs
    검증을 포함한다)."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_portability_phase_qa_checklist_doc_references_existing_scripts():
    """문서가 가리키는 자동 검사 스크립트가 실제로 저장소에 존재한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for script in REFERENCED_SCRIPTS:
        assert script in content, f"missing script reference: {script}"
        assert (REPO_ROOT / script).is_file(), f"referenced script missing: {script}"


def test_portability_phase_qa_checklist_doc_references_existing_docs():
    """문서가 가리키는 관련 Phase A 문서가 실제로 존재한다(링크 깨짐 없음)."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for doc in REFERENCED_DOCS:
        assert doc in content, f"missing doc reference: {doc}"
        assert (REPO_ROOT / doc).is_file(), f"referenced doc missing: {doc}"


def test_portability_phase_qa_checklist_doc_lists_all_twelve_modules():
    """manifest 절이 docs/modules.md 기준 12개 모듈을 모두 나열한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for module in [
        "document",
        "revision",
        "parser",
        "render",
        "acl",
        "discussion",
        "search",
        "cache",
        "jobs",
        "user",
        "admin",
        "audit",
    ]:
        assert f"`{module}`" in content, f"missing module reference: {module}"


def test_boundary_and_manifest_checks_are_already_wired_into_qa():
    """boundary/manifest 검사가 이미 scripts/qa.sh 게이트에 연결되어
    있다는 문서의 주장이 실제 스크립트 내용과 맞는지 확인한다."""
    qa_contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
    for script in [
        "scripts/check_boundaries.py",
        "scripts/check_no_app_import_in_modules.py",
        "scripts/check_module_manifests.py",
    ]:
        assert script in qa_contents, f"expected {script} to already be wired into qa.sh"


def test_contract_drift_report_is_not_wired_into_qa():
    """drift 리포트는 정보성 스크립트라 scripts/qa.sh 에 연결돼 있지
    않다는 docs/contract-drift-report.md 의 기존 방침과 이 문서가
    모순되지 않는다."""
    qa_contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "scripts/check_contract_drift.py" not in qa_contents
