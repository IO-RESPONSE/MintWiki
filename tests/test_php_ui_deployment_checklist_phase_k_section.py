"""`docs/php-ui-deployment-checklist.md`의 Phase K 확인 절(12절, 태스크
0718)이 acceptance criteria가 요구하는 확인 항목(문서 삭제 lifecycle,
`/admin/audit` 실제 이벤트, `/admin/backup` 다운로드, `/admin/diagnostics`
실데이터+export)을 실제로 다루고, 이를 검증하는 자동화(스모크 스크립트/
테스트)를 정확히 가리키는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-ui-deployment-checklist.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_deployment_checklist_has_phase_k_section():
    content = _content()

    assert "## 12. Phase K 확인 (삭제 + 감사 로그 + 백업 다운로드 + 진단, 0714-0717)" in content
    assert "### 12.1 Phase K 자산 배포 확인" in content
    assert "### 12.2 문서 삭제 확인" in content
    assert "### 12.3 감사 로그 확인" in content
    assert "### 12.4 백업 다운로드 확인" in content
    assert "### 12.5 운영 진단 확인" in content


def test_deployment_checklist_phase_k_section_covers_acceptance_criteria_terms():
    content = _content()

    assert "confirm_delete" in content
    assert "/wiki/{title}/delete" in content
    assert "/admin/audit" in content
    assert "auth.login_succeeded" in content
    assert "/admin/backup/download/{name}" in content
    assert "traversal" in content
    assert "/admin/diagnostics/export" in content


def test_deployment_checklist_phase_k_section_references_existing_automation():
    """체크리스트가 언급하는 자동화(스모크 스크립트/테스트)는 실제로
    저장소에 존재해야 한다 — 문서가 존재하지 않는 스크립트를 가리키면
    안 된다."""
    content = _content()

    assert "UiPhaseKSmokeTest.php" in content
    assert "DocumentDeleteRouteTest.php" in content
    assert "PdoAuditRecorderTest.php" in content
    assert "BackupDownloadRouteTest.php" in content
    assert "DiagnosticsExportRouteTest.php" in content
    assert "phase_k_anonymous_delete_denied_check" in content
    assert "phase_k_document_delete_check" in content
    assert "phase_k_audit_log_check" in content
    assert "phase_k_backup_download_check" in content
    assert "phase_k_backup_download_traversal_check" in content
    assert "phase_k_diagnostics_real_data_check" in content
    assert "phase_k_diagnostics_export_check" in content
    assert "test_php_deployment_package_manifest_covers_phase_k_assets" in content

    assert (REPO_ROOT / "php" / "tests" / "Http" / "UiPhaseKSmokeTest.php").is_file()
    assert (REPO_ROOT / "php" / "scripts" / "smoke-ui-phase-k.sh").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "DocumentDeleteRouteTest.php").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Modules" / "Audit" / "PdoAuditRecorderTest.php").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "BackupDownloadRouteTest.php").is_file()
    assert (REPO_ROOT / "php" / "tests" / "Http" / "DiagnosticsExportRouteTest.php").is_file()
    assert (REPO_ROOT / "php" / "scripts" / "live-e2e-smoke-test.sh").is_file()


def test_deployment_checklist_numbering_still_ends_with_out_of_scope_and_related_docs():
    """새 절을 12번으로 끼워 넣으면서 기존 "다루지 않는 것"/"관련 문서" 절이
    밀렸는지 확인한다 — 정확한 절 번호 자체보다 "Phase K 확인 다음에 최소
    하나 이상의 절을 거쳐 다루지 않는 것/관련 문서로 끝난다"는 상대 순서를
    확인한다(0695/0713 테스트가 먼저 세운 관례)."""
    content = _content()

    assert "## 12. Phase K 확인" in content
    assert "## 관련 문서" in content
    assert "## 12. 이 체크리스트가 다루지 않는 것" not in content

    phase_k_index = content.index("## 12. Phase K 확인")
    related_docs_index = content.index("## 관련 문서")
    out_of_scope_index = content.index("이 체크리스트가 다루지 않는 것")
    assert phase_k_index < out_of_scope_index < related_docs_index
