"""`docs/php-replacement-readiness-checklist.md` 가 태스크 0388 의 목표
("PHP 전환 준비 체크리스트를 추가한다")와 Notes 요구사항("모듈별
ready/not-ready 기준을 둔다")을 실제로 고정하고 있으며, 그 체크리스트가
`docs/php-replacement-strategy.md` 의 readiness gate 5개, 그리고 저장소에
실제로 존재하는 모듈 목록과 어긋나지 않는지 확인한다.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-replacement-readiness-checklist.md"
STRATEGY_DOC_PATH = REPO_ROOT / "docs" / "php-replacement-strategy.md"
MODULES_ROOT = REPO_ROOT / "src" / "modules"

REQUIRED_DOC_HEADINGS = [
    "## Gate 1: 모듈 계약 manifest 존재 + 검증 통과",
    "## Gate 2: 도메인 경계 검사 통과",
    "## Gate 3: fixture parity 커버리지",
    "## Gate 4: error code 상수화",
    "## Gate 5: PostgreSQL 비의존 (ANSI SQL + MariaDB 호환)",
    "## Ready 판정 규칙",
    "## 모듈별 상태 (Phase A 시점 스냅샷)",
    "## 이 문서가 하지 않는 것",
]


def _module_names():
    return sorted(
        path.name
        for path in MODULES_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith("__")
    )


def test_php_replacement_readiness_checklist_doc_exists():
    """PHP 전환 준비 체크리스트 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_replacement_readiness_checklist_doc_has_required_sections():
    """5개 gate, ready 판정 규칙, 모듈별 상태, 범위 제외 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_replacement_readiness_checklist_doc_has_checkbox_items_per_gate():
    """각 gate 절 안에 실제로 체크할 수 있는 checkbox 항목이 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    gate_headings = [h for h in REQUIRED_DOC_HEADINGS if h.startswith("## Gate")]
    sections = content.split("## ")
    for heading in gate_headings:
        title = heading[len("## ") :]
        matches = [s for s in sections if s.startswith(title)]
        assert matches, f"gate section not found: {heading}"
        assert "- [ ]" in matches[0], f"gate section has no checklist items: {heading}"


def test_php_replacement_readiness_checklist_doc_defines_ready_requires_all_gates():
    """ready 판정이 5개 gate 전부 충족과 PHP parity test 통과를 요구한다는
    것을 명시한다(부분 충족은 ready 가 아님)."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "전부" in content
    assert "parity test" in content
    assert "not-ready" in content or "not ready" in content


def test_php_replacement_readiness_checklist_doc_covers_every_existing_module():
    """저장소에 실제로 존재하는 모든 모듈이 모듈별 상태 표에 등장한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for name in _module_names():
        assert f"| {name} |" in content, f"module missing from status table: {name}"


def test_php_replacement_readiness_checklist_doc_snapshot_matches_manifest_status():
    """Phase A 시점 스냅샷이 실제 manifest.json 의 port.status 와 어긋나지
    않는다 — 모든 모듈이 not_started 이면 문서도 전부 not ready 로
    표시해야 한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for name in _module_names():
        manifest_path = MODULES_ROOT / name / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        status = manifest["port"]["status"]
        row_lines = [
            line for line in content.splitlines() if line.startswith(f"| {name} |")
        ]
        assert row_lines, f"module missing from status table: {name}"
        row = row_lines[0]
        if status == "not_started":
            assert "not ready" in row, f"{name} row should read not ready: {row}"


def test_php_replacement_readiness_checklist_doc_references_related_docs():
    """전략/parity 계획/manifest 스키마/error code/모듈 목록/용어 문서와
    연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-replacement-strategy.md",
        "docs/php-parity-test-plan.md",
        "docs/module-contract-manifest-schema.md",
        "docs/portable-exception-code-policy.md",
        "docs/modules.md",
        "docs/portability-glossary.md",
        "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"


def test_php_replacement_readiness_checklist_doc_matches_strategy_gate_count():
    """이 체크리스트의 gate 5개가 `docs/php-replacement-strategy.md` 의
    readiness gate 목록(5개 조건)과 수가 일치한다."""
    strategy_content = STRATEGY_DOC_PATH.read_text(encoding="utf-8")
    assert "## PHP 전환 기준 (모듈별 readiness gate)" in strategy_content
    gate_section = strategy_content.split(
        "## PHP 전환 기준 (모듈별 readiness gate)"
    )[1].split("\n## ")[0]
    numbered_items = [
        line for line in gate_section.splitlines() if line.strip()[:2] in (
            "1.", "2.", "3.", "4.", "5.",
        )
    ]
    assert len(numbered_items) == 5

    checklist_content = DOC_PATH.read_text(encoding="utf-8")
    assert checklist_content.count("## Gate ") == 5


def test_php_replacement_readiness_checklist_doc_does_not_own_the_live_matrix():
    """모듈별 최신 상태를 계속 갱신하는 살아있는 matrix(0433 의 범위)를
    이 문서가 자기 것이라고 주장하지 않는다는 범위 제외를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "0433" in content
