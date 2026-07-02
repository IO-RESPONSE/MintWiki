"""`docs/php-replacement-readiness-gate.md` 가 태스크 0440 의 목표("PHP
전환 gate 문서를 추가한다")와 Notes 요구사항("DB 단계로 넘어가기 전
완료 조건을 명시한다")을 실제로 고정하고 있으며, 그 gate 조건이 가리키는
문서/스크립트가 실제로 존재하고 서로 어긋나지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-replacement-readiness-gate.md"

REQUIRED_DOC_HEADINGS = [
    "## 이 gate 가 판정하지 않는 것 (범위 구분)",
    "## Gate 조건",
    "## 재판정 방법",
    "## 이 문서 작성 시점 스냅샷 (Phase B 종료, 0391-0440)",
    "## 이 문서가 하지 않는 것",
    "## 관련 문서",
]

REFERENCED_DOCS = [
    "docs/php-replacement-strategy.md",
    "docs/php-replacement-readiness-checklist.md",
    "docs/php-module-replacement-matrix.md",
    "docs/php-runtime-phase-qa-checklist.md",
    "docs/php-runtime-security-baseline.md",
    "docs/contract-drift-report.md",
    "docs/php-db-ui-micro-job-prompts-0351-0670.md",
]

REFERENCED_SCRIPTS = [
    "scripts/check_boundaries.py",
    "scripts/check_no_app_import_in_modules.py",
    "scripts/check_module_manifests.py",
    "scripts/test.sh",
    "scripts/qa.sh",
    "php/scripts/qa.sh",
]


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_php_replacement_readiness_gate_doc_exists():
    """PHP 전환 gate 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_replacement_readiness_gate_doc_has_required_sections():
    """범위 구분, gate 조건, 재판정 방법, 스냅샷, 범위 제외, 관련 문서
    절이 모두 있다."""
    content = _doc_text()
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_replacement_readiness_gate_doc_has_seven_numbered_conditions():
    """Gate 조건 절 안에 번호가 매겨진 조건 항목이 있다(전부 충족을
    요구하는 gate 이므로 항목이 명시적으로 나열되어야 한다)."""
    content = _doc_text()
    gate_section = content.split("## Gate 조건")[1].split("\n## ")[0]
    for n in range(1, 8):
        assert f"{n}. **" in gate_section, f"missing numbered condition {n}"


def test_php_replacement_readiness_gate_doc_states_db_phase_transition():
    """DB 단계(Phase C)로 넘어가기 전 완료 조건을 명시한다는 Notes
    요구사항이 실제로 본문에 있다."""
    content = _doc_text()
    assert "Phase C" in content
    assert "0441-0520" in content


def test_php_replacement_readiness_gate_doc_declares_a_verdict():
    """gate 판정 결과(PASS/FAIL)를 실제로 명시한다 — 조건만 나열하고
    판정을 내리지 않는 문서가 되지 않도록 한다."""
    content = _doc_text()
    assert "판정: PASS" in content or "판정: FAIL" in content


def test_php_replacement_readiness_gate_doc_does_not_require_full_module_parity():
    """Phase C 시작 조건이 모듈별 parity/pass 상태 도달을 요구하지
    않는다는 것을 명시한다(구조적으로 불가능하므로)."""
    content = _doc_text()
    assert "parity" in content and "pass" in content
    assert "구조적으로" in content and "불가능" in content


def test_php_replacement_readiness_gate_doc_references_existing_docs():
    """문서가 가리키는 관련 문서가 실제로 존재한다(링크 깨짐 없음)."""
    content = _doc_text()
    for doc in REFERENCED_DOCS:
        assert doc in content, f"missing doc reference: {doc}"
        assert (REPO_ROOT / doc).is_file(), f"referenced doc missing: {doc}"


def test_php_replacement_readiness_gate_doc_references_existing_scripts():
    """문서가 재판정 방법으로 제시하는 스크립트가 실제로 존재한다."""
    content = _doc_text()
    for script in REFERENCED_SCRIPTS:
        assert script in content, f"missing script reference: {script}"
        assert (REPO_ROOT / script).is_file(), f"referenced script missing: {script}"


def test_php_replacement_readiness_gate_doc_all_phase_b_tasks_done():
    """gate 조건 6("Phase B 태스크 전량 완료")이 실제로 성립한다 —
    0391-0439가 모두 tasks/done 에 존재해야 한다(0440은 이 문서를 추가하는
    태스크 자신이라 done 디렉터리 검사에서 제외한다)."""
    done_dir = REPO_ROOT / "tasks" / "done"
    done_names = {p.name for p in done_dir.iterdir()}
    for task_id in range(391, 440):
        prefix = f"{task_id:04d}-"
        assert any(
            name.startswith(prefix) for name in done_names
        ), f"Phase B task {task_id} not found in tasks/done"
