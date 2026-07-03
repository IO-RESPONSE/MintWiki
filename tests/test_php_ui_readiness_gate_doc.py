"""`docs/php-ui-readiness-gate.md` 가 태스크 0570 의 목표("UI readiness gate 문서를 추가한다")
와 Notes 요구사항("웹호스팅 배포 전 UI 완료 조건을 둔다")을 실제로 고정하고 있으며,
그 gate 조건이 가리키는 문서/스크립트가 실제로 존재하고 서로 어긋나지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-ui-readiness-gate.md"

REQUIRED_DOC_HEADINGS = [
    "## 이 gate가 판정하지 않는 것 (범위 구분)",
    "## Gate 조건",
    "## 재판정 방법",
    "## 이 문서 작성 시점 스냅샷 (Phase D 종료, 0521-0610)",
    "## Phase D 진입 시 필수 인식 사항 (UI 개발자 필독)",
    "## Phase D 완료 체크리스트",
    "## Gate 미통과 시 조치",
    "## 다음 단계로의 전환 (Phase E Handoff)",
    "## 관련 문서",
]

REFERENCED_DOCS = [
    "docs/php-ui-phase-qa-checklist.md",
    "docs/php-ui-architecture.md",
    "docs/php-static-asset-serving.md",
    "docs/php-runtime-security-baseline.md",
    "docs/php-runtime-phase-qa-checklist.md",
    "docs/db-phase-readiness-gate.md",
    "docs/php-replacement-readiness-gate.md",
    "docs/shared-hosting-migration-policy.md",
    "docs/db-web-hosting-constraints.md",
    "docs/php-db-ui-micro-job-prompts-0351-0670.md",
]

REFERENCED_SCRIPTS = [
    "scripts/test.sh",
    "scripts/qa.sh",
    "php/scripts/qa.sh",
]


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_php_ui_readiness_gate_doc_exists():
    """PHP UI readiness gate 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_ui_readiness_gate_doc_has_required_sections():
    """범위 구분, gate 조건, 재판정 방법, 스냅샷, 필수 인식 사항, 체크리스트,
    미통과 조치, 다음 단계 전환, 관련 문서 절이 모두 있다."""
    content = _doc_text()
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_ui_readiness_gate_doc_has_seven_numbered_conditions():
    """Gate 조건 절 안에 번호가 매겨진 조건 항목이 있다(전부 충족을
    요구하는 gate 이므로 항목이 명시적으로 나열되어야 한다)."""
    content = _doc_text()
    gate_section = content.split("## Gate 조건")[1].split("\n## ")[0]
    for n in range(1, 8):
        assert f"{n}. **" in gate_section, f"missing numbered condition {n}"


def test_php_ui_readiness_gate_doc_states_webhosting_deployment_condition():
    """웹호스팅 배포 전 UI 완료 조건을 명시한다는 Notes 요구사항이 실제로
    본문에 있다."""
    content = _doc_text()
    assert "웹호스팅" in content
    assert "배포" in content


def test_php_ui_readiness_gate_doc_declares_a_verdict():
    """gate 판정 결과(PASS/FAIL)를 실제로 명시한다 — 조건만 나열하고
    판정을 내리지 않는 문서가 되지 않도록 한다."""
    content = _doc_text()
    assert "판정: PASS" in content or "판정: FAIL" in content


def test_php_ui_readiness_gate_doc_mentions_phase_d_and_e():
    """Phase D 완료와 Phase E 진입 조건을 모두 언급한다."""
    content = _doc_text()
    assert "Phase D" in content
    assert "Phase E" in content
    assert "0521-0610" in content
    assert "0611" in content


def test_php_ui_readiness_gate_doc_references_existing_docs():
    """문서가 가리키는 관련 문서가 실제로 존재한다(링크 깨짐 없음)."""
    content = _doc_text()
    for doc in REFERENCED_DOCS:
        assert doc in content, f"missing doc reference: {doc}"
        assert (REPO_ROOT / doc).is_file(), f"referenced doc missing: {doc}"


def test_php_ui_readiness_gate_doc_references_existing_scripts():
    """문서가 재판정 방법으로 제시하는 스크립트가 실제로 존재한다."""
    content = _doc_text()
    for script in REFERENCED_SCRIPTS:
        assert script in content, f"missing script reference: {script}"
        assert (REPO_ROOT / script).is_file(), f"referenced script missing: {script}"


def test_php_ui_readiness_gate_doc_mentions_routing_and_template_completeness():
    """Gate 조건에 UI 라우터와 템플릿 완성도 요구사항이 있다."""
    content = _doc_text()
    assert "라우터" in content
    assert "템플릿" in content
    assert "/documents/" in content


def test_php_ui_readiness_gate_doc_mentions_html_escaping():
    """Gate 조건에 HTML escaping 정책 준수 요구사항이 있다."""
    content = _doc_text()
    assert "HTML Escaping" in content or "escaping" in content
    assert "htmlspecialchars" in content


def test_php_ui_readiness_gate_doc_mentions_csrf_defense():
    """Gate 조건에 CSRF 방어 기초 요구사항이 있다."""
    content = _doc_text()
    assert "CSRF" in content


def test_php_ui_readiness_gate_doc_mentions_security_headers():
    """Gate 조건에 보안 HTTP 헤더 요구사항이 있다."""
    content = _doc_text()
    assert "X-Content-Type-Options" in content or "security header" in content


def test_php_ui_readiness_gate_doc_mentions_mobile_responsive():
    """Gate 조건에 모바일 반응형 기초 요구사항이 있다."""
    content = _doc_text()
    assert "모바일" in content
    assert "viewport" in content


def test_php_ui_readiness_gate_doc_mentions_accessibility():
    """Gate 조건에 접근성 기초 요구사항이 있다."""
    content = _doc_text()
    assert "접근성" in content or "WCAG" in content
    assert "lang=" in content or "landmark" in content


def test_php_ui_readiness_gate_doc_mentions_phase_d_vs_e_boundary():
    """Gate가 Phase D와 Phase E의 경계를 명시한다."""
    content = _doc_text()
    assert "Phase E" in content
    assert "Handoff" in content or "전환" in content
