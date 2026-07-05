"""`docs/php-ui-deployment-checklist.md`의 Phase J 확인 절(11절, 태스크
0713)이 acceptance criteria가 요구하는 확인 항목(NamuMark 렌더, 편집
화면의 요약/미리보기/툴바/문법 도움말, history/discussion 200)을 실제로
다루고, 이를 검증하는 자동화(스모크 스크립트/테스트)를 정확히 가리키는지
확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-ui-deployment-checklist.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_deployment_checklist_has_phase_j_section():
    content = _content()

    assert "## 11. Phase J 확인 (NamuMark 렌더 + 편집 UX + history/discussion, 0704-0712)" in content
    assert "### 11.1 Phase J 자산 배포 확인" in content
    assert "### 11.2 NamuMark 렌더 확인" in content
    assert "### 11.3 편집 화면 확인" in content
    assert "### 11.4 history 확인" in content
    assert "### 11.5 discussion 확인" in content


def test_deployment_checklist_phase_j_section_covers_acceptance_criteria_terms():
    content = _content()

    assert "<strong>" in content
    assert "<table>" in content
    assert 'class="toc"' in content
    assert "edit-preview" in content
    assert "editor-toolbar" in content
    assert "editor-help" in content
    assert "/wiki/{title}/history" in content
    assert "/wiki/{title}/discussion" in content


def test_deployment_checklist_phase_j_section_references_existing_automation():
    """체크리스트가 언급하는 자동화(스모크 스크립트/테스트)는 실제로
    저장소에 존재해야 한다 — 문서가 존재하지 않는 스크립트를 가리키면
    안 된다."""
    content = _content()

    assert "smoke-ui-phase-j.sh" in content
    assert "UiPhaseJSmokeTest.php" in content
    assert "DocumentViewNamuMarkRouteTest.php" in content
    assert "EditSummaryFieldTest.php" in content
    assert "DocumentEditPreviewRouteTest.php" in content
    assert "DocumentHistoryDiffRouteTest.php" in content
    assert "DiscussionRouteTest.php" in content
    assert "phase_j_namumark_render_check" in content
    assert "phase_j_edit_ux_check" in content
    assert "phase_j_history_route_check" in content
    assert "phase_j_discussion_route_check" in content
    assert "phase_j_discussion_write_check" in content
    assert "phase_j_comment_write_check" in content
    assert "test_php_deployment_package_manifest_covers_phase_j_assets" in content

    assert (REPO_ROOT / "php" / "scripts" / "smoke-ui-phase-j.sh").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "UiPhaseJSmokeTest.php").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "DocumentViewNamuMarkRouteTest.php").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "EditSummaryFieldTest.php").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "DocumentEditPreviewRouteTest.php").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "DocumentHistoryDiffRouteTest.php").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "DiscussionRouteTest.php").is_file()


def test_deployment_checklist_numbering_still_ends_with_out_of_scope_and_related_docs():
    """새 절을 11번으로 끼워 넣으면서 기존 "다루지 않는 것"/"관련 문서" 절
    번호가 밀렸는지 확인한다."""
    content = _content()

    assert "## 12. 이 체크리스트가 다루지 않는 것" in content
    assert "## 관련 문서" in content
    assert "## 11. 이 체크리스트가 다루지 않는 것" not in content
