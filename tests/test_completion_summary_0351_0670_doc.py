"""`docs/completion-summary-0351-0670.md` 가 태스크 0670의 목표("0351-0670
완료 요약 문서를 추가한다")와 Notes 요구사항("남은 기능과 위험을 다음
큐로 넘긴다")을 실제로 고정하고 있으며, 문서가 가리키는 Phase별 요약/QA/
gate 문서가 실제로 존재하는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "completion-summary-0351-0670.md"

REQUIRED_DOC_HEADINGS = [
    "## 목적",
    "## 1. Phase별 요약",
    "## 2. 이 구간이 보장하는 것",
    "## 3. 아직 실제 구현이 아닌 것 (다음 큐로 넘기는 위험)",
    "## 4. 다음 큐 권장 순서",
    "## 5. 검사 및 검증",
    "## 6. 관련 문서",
]

REFERENCED_DOCS = [
    "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    "docs/php-replacement-readiness-checklist.md",
    "docs/portability-phase-qa-checklist.md",
    "docs/php-runtime-phase-qa-checklist.md",
    "docs/php-replacement-readiness-gate.md",
    "docs/ansi-db-phase-summary.md",
    "docs/db-phase-qa-checklist.md",
    "docs/db-phase-readiness-gate.md",
    "docs/php-ui-phase-summary.md",
    "docs/php-ui-phase-qa-checklist.md",
    "docs/php-ui-readiness-gate.md",
    "docs/hosting-phase-qa-checklist.md",
    "docs/production-readiness-report.md",
    "docs/portable-restore-plan.md",
    "docs/shared-hosting-rollback-procedure.md",
    "docs/final-python-to-php-cutover-plan.md",
    "php/scripts/README.md",
]

REQUIRED_NEXT_QUEUE_RANGES = [
    "0671-0740",
    "0741-0800",
    "0801-0850",
]

REQUIRED_QA_COMMANDS = [
    "scripts/test.sh",
    "scripts/qa.sh",
]


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_completion_summary_doc_exists():
    """0351-0670 완료 요약 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_completion_summary_doc_has_required_sections():
    """Phase별 요약, 보장 사항, 남은 위험, 다음 큐 순서, QA, 관련 문서
    절이 모두 있다."""
    content = _doc_text()
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_completion_summary_doc_references_existing_docs():
    """문서가 가리키는 Phase별 요약/QA/gate 문서가 실제로 존재한다(링크
    깨짐 없음)."""
    content = _doc_text()
    for doc in REFERENCED_DOCS:
        assert doc in content, f"missing doc reference: {doc}"
        assert (REPO_ROOT / doc).is_file(), f"referenced doc missing: {doc}"


def test_completion_summary_doc_hands_off_remaining_risk_to_next_queue():
    """Notes 요구사항("남은 기능과 위험을 다음 큐로 넘긴다")에 따라 다음
    큐 권장 범위가 문서에 명시되어 있다."""
    content = _doc_text()
    for queue_range in REQUIRED_NEXT_QUEUE_RANGES:
        assert queue_range in content, f"missing next queue range: {queue_range}"


def test_completion_summary_doc_references_qa_commands():
    """문서가 가리키는 QA 명령이 실제로 저장소에 존재한다."""
    content = _doc_text()
    for command in REQUIRED_QA_COMMANDS:
        assert command in content, f"missing qa command reference: {command}"
        assert (REPO_ROOT / command).is_file(), f"referenced qa command missing: {command}"
