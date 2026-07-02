"""`docs/contract-drift-report.md` 가 태스크 0389 의 Notes 요구사항
("초기에는 문서/스크립트 골격만 둔다")을 실제로 고정하고 있으며, 문서가
설명하는 실행 방법과 리포트 스크립트(`scripts/check_contract_drift.py`)
의 동작이 어긋나지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "contract-drift-report.md"
QA_SCRIPT_PATH = REPO_ROOT / "scripts" / "qa.sh"
DRIFT_SCRIPT_PATH = REPO_ROOT / "scripts" / "check_contract_drift.py"

REQUIRED_DOC_HEADINGS = [
    "## Contract drift 정의",
    "## 현재 상태: 측정 불가 (php/ 트리 없음)",
    "## 실행 방법",
    "## 이후 확장 (이 태스크의 범위 밖)",
    "## 이 문서가 하지 않는 것",
]


def test_contract_drift_report_doc_exists():
    """drift 리포트 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_contract_drift_report_doc_has_required_sections():
    """정의, 현재 상태, 실행 방법, 확장 계획, 범위 제외 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_contract_drift_report_doc_references_the_script():
    """문서가 실제 리포트 스크립트 경로를 실행 방법으로 안내한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "scripts/check_contract_drift.py" in content


def test_contract_drift_script_exists():
    """문서가 가리키는 리포트 스크립트가 실제로 존재한다."""
    assert DRIFT_SCRIPT_PATH.is_file()


def test_contract_drift_report_doc_declares_not_wired_to_qa():
    """문서가 스스로 밝힌 대로, 이 스크립트는 아직 scripts/qa.sh 게이트에
    연결돼 있지 않다 (정보성 리포트이므로 실패 기준이 없다는 이 태스크의
    설계 결정)."""
    qa_contents = QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "scripts/check_contract_drift.py" not in qa_contents


def test_contract_drift_report_doc_references_related_docs():
    """기존 전략/manifest/namespace/parity/readiness/용어 문서와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-replacement-strategy.md" in content
    assert "docs/module-contract-manifest-schema.md" in content
    assert "docs/php-namespace-mapping.md" in content
    assert "docs/php-parity-test-plan.md" in content
    assert "docs/php-replacement-readiness-checklist.md" in content
    assert "docs/portability-glossary.md" in content
