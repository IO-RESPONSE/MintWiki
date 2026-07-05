"""`docs/php-ui-deployment-checklist.md`의 스킨(Skin) 확인 절(9절, 태스크
0695)이 acceptance criteria가 요구하는 확인 항목(상단바 노출, 브랜드색
#008485 적용, 문서 액션 탭, 반응형)을 실제로 다루고, 이를 검증하는
자동화(스모크 스크립트/테스트)를 정확히 가리키는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-ui-deployment-checklist.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_deployment_checklist_has_skin_section():
    content = _content()

    assert "## 9. 스킨(Skin) 확인 (Phase H: NamuWiki-style Skin, 0689-0694)" in content
    assert "### 9.1 스킨 자산 배포 확인" in content
    assert "### 9.2 상단바 노출 확인" in content
    assert "### 9.3 브랜드색 `#008485` 적용 확인" in content
    assert "### 9.4 문서 액션 탭 확인" in content
    assert "### 9.5 반응형(Responsive) 확인" in content


def test_deployment_checklist_skin_section_covers_acceptance_criteria_terms():
    content = _content()

    assert "site-nav" in content
    assert "#008485" in content
    assert "document-tabs" in content
    assert "@media (max-width: 640px)" in content


def test_deployment_checklist_skin_section_references_existing_automation():
    """체크리스트가 언급하는 자동화(스모크 스크립트/테스트)는 실제로
    저장소에 존재해야 한다 — 문서가 존재하지 않는 스크립트를 가리키면
    안 된다."""
    content = _content()

    assert "smoke-ui-skin.sh" in content
    assert "UiSkinSmokeTest.php" in content
    assert "live-e2e-smoke-test.sh" in content
    assert "skin_top_bar_and_brand_check" in content
    assert "skin_document_action_tabs_check" in content
    assert "skin_responsive_asset_check" in content
    assert "test_php_deployment_package_manifest_covers_skin_assets" in content

    assert (REPO_ROOT / "php" / "scripts" / "smoke-ui-skin.sh").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "UiSkinSmokeTest.php").is_file()


def test_deployment_checklist_numbering_still_ends_with_out_of_scope_and_related_docs():
    """새 절을 9번으로 끼워 넣으면서 기존 "다루지 않는 것"/"관련 문서" 절
    번호가 밀렸는지 확인한다."""
    content = _content()

    assert "## 10. 관리자 콘솔 확인" in content
    assert "## 11. 이 체크리스트가 다루지 않는 것" in content
    assert "## 관련 문서" in content
    assert "## 9. 이 체크리스트가 다루지 않는 것" not in content
