"""`docs/hosting-phase-qa-checklist.md` 가 태스크 0669 의 목표("hosting
phase QA 체크리스트를 추가한다")와 Notes 요구사항("installer/package/
security/rollback을 점검한다")을 실제로 고정하고 있으며, 체크리스트가
가리키는 스크립트/문서/테스트가 실제로 존재하고 서로 어긋나지 않는지
확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "hosting-phase-qa-checklist.md"
ROOT_QA_SCRIPT_PATH = REPO_ROOT / "scripts" / "qa.sh"
PHP_QA_SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "qa.sh"

REQUIRED_DOC_HEADINGS = [
    "## 사용법",
    "## 1. Installer",
    "## 2. Package",
    "## 3. Security",
    "## 4. Rollback",
    "## 이 체크리스트가 다루지 않는 것",
    "## 관련 문서",
]

REFERENCED_SCRIPTS = [
    "php/scripts/qa.sh",
]

REFERENCED_DOCS = [
    "docs/php-runtime-phase-qa-checklist.md",
    "docs/db-phase-qa-checklist.md",
    "docs/php-ui-phase-qa-checklist.md",
    "docs/shared-hosting-qa-checklist.md",
    "docs/shared-hosting-security-checklist.md",
    "docs/shared-hosting-rollback-procedure.md",
    "docs/php-ui-rollback-checklist.md",
    "docs/final-python-to-php-cutover-plan.md",
    "docs/installer-lock-file-policy.md",
    "docs/php-ui-installer-link-policy.md",
    "docs/no-composer-hosting-deployment.md",
    "docs/composer-hosting-deployment.md",
    "docs/shared-hosting-session-policy.md",
    "docs/cookie-security-policy.md",
    "docs/shared-hosting-provider-checklist-samples.md",
    "docs/shared-hosting-performance-checklist.md",
    "docs/php-db-ui-micro-job-prompts-0351-0670.md",
]

REFERENCED_PHP_SOURCE_FILES = [
    "php/src/Installer/InstallerRouteGate.php",
    "php/src/Installer/InstallerLock.php",
    "php/src/Ui/InstallWelcomePage.php",
    "php/src/Ui/InstallRequiredPage.php",
    "php/src/Ui/InstallDBFormPage.php",
    "php/src/Ui/InstallAdminAccountFormPage.php",
    "php/src/Ui/InstallCompletionPage.php",
    "php/src/Security/PathTraversalGuard.php",
    "php/src/Security/BackupDownloadGuard.php",
    "php/src/Security/CsrfTokenService.php",
    "php/src/Security/PhpSessionAdapter.php",
    "php/src/App/MaintenanceModeConfig.php",
]

REFERENCED_PHP_TEST_FILES = [
    "php/tests/Persistence/InstallerRouteGateTest.php",
    "php/tests/Persistence/InstallerLockTest.php",
    "php/tests/Persistence/InstallerRequirementCheckTest.php",
    "php/tests/Persistence/InstallerDBCheckTest.php",
    "php/tests/Persistence/InstallerSchemaApplyTest.php",
    "php/tests/Ui/InstallWelcomePageTest.php",
    "php/tests/Ui/InstallRequiredPageTest.php",
    "php/tests/Ui/InstallDBFormPageTest.php",
    "php/tests/Ui/InstallAdminAccountFormPageTest.php",
    "php/tests/Ui/InstallCompletionPageTest.php",
    "php/tests/Security/PathTraversalGuardTest.php",
    "php/tests/Security/BackupDownloadGuardTest.php",
    "php/tests/Security/CsrfTokenServiceTest.php",
    "php/tests/Security/PhpSessionAdapterTest.php",
    "php/tests/Http/HtmlSecurityHeadersTest.php",
]

REFERENCED_PHP_OTHER_FILES = [
    "php/deployment-package-manifest.json",
    "php/scripts/build-package.sh",
    "php/scripts/post-cutover-validate.sh",
    "php/scripts/README.md",
]

REFERENCED_PYTHON_TEST_FILES = [
    "tests/test_php_deployment_package_manifest.py",
    "tests/test_php_package_build_script.py",
    "tests/test_php_ui_rollback_checklist_doc.py",
    "tests/test_final_python_to_php_cutover_plan_doc.py",
    "tests/test_php_post_cutover_validation_script.py",
]


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_hosting_phase_qa_checklist_doc_exists():
    """Phase E QA 체크리스트 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_hosting_phase_qa_checklist_doc_has_required_sections():
    """사용법, installer/package/security/rollback 4개 검증 절, 범위
    제외, 관련 문서 절이 모두 있다(Notes: installer/package/security/
    rollback을 점검한다)."""
    content = _doc_text()
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_hosting_phase_qa_checklist_doc_references_existing_scripts():
    """문서가 가리키는 자동 검사 스크립트가 실제로 저장소에 존재한다."""
    content = _doc_text()
    for script in REFERENCED_SCRIPTS:
        assert script in content, f"missing script reference: {script}"
        assert (REPO_ROOT / script).is_file(), f"referenced script missing: {script}"


def test_hosting_phase_qa_checklist_doc_references_existing_docs():
    """문서가 가리키는 관련 문서가 실제로 존재한다(링크 깨짐 없음)."""
    content = _doc_text()
    for doc in REFERENCED_DOCS:
        assert doc in content, f"missing doc reference: {doc}"
        assert (REPO_ROOT / doc).is_file(), f"referenced doc missing: {doc}"


def test_hosting_phase_qa_checklist_doc_references_existing_php_source_files():
    """문서가 가리키는 PHP 소스 파일이 실제로 존재한다."""
    content = _doc_text()
    for source_file in REFERENCED_PHP_SOURCE_FILES:
        assert source_file in content, f"missing php source reference: {source_file}"
        assert (REPO_ROOT / source_file).is_file(), f"referenced php source missing: {source_file}"


def test_hosting_phase_qa_checklist_doc_references_existing_php_tests():
    """문서가 가리키는 PHP 테스트 파일이 실제로 존재한다."""
    content = _doc_text()
    for test_file in REFERENCED_PHP_TEST_FILES:
        assert test_file in content, f"missing php test reference: {test_file}"
        assert (REPO_ROOT / test_file).is_file(), f"referenced php test missing: {test_file}"


def test_hosting_phase_qa_checklist_doc_references_existing_php_other_files():
    """문서가 가리키는 PHP manifest/스크립트/README가 실제로 존재한다."""
    content = _doc_text()
    for other_file in REFERENCED_PHP_OTHER_FILES:
        assert other_file in content, f"missing php file reference: {other_file}"
        assert (REPO_ROOT / other_file).is_file(), f"referenced php file missing: {other_file}"


def test_hosting_phase_qa_checklist_doc_references_existing_python_tests():
    """문서가 가리키는 파이썬 QA 테스트가 실제로 존재한다."""
    content = _doc_text()
    for test_file in REFERENCED_PYTHON_TEST_FILES:
        assert test_file in content, f"missing python test reference: {test_file}"
        assert (REPO_ROOT / test_file).is_file(), f"referenced python test missing: {test_file}"


def test_php_qa_hook_is_already_wired_into_root_qa():
    """php/scripts/qa.sh가 이미 루트 scripts/qa.sh에서 선택 실행되도록
    연결되어 있다는 문서의 주장이 실제 스크립트 내용과 맞는지 확인한다
    (0431)."""
    root_qa_contents = ROOT_QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "php/scripts/qa.sh" in root_qa_contents


def test_php_qa_sh_wires_test_sh():
    """php/scripts/qa.sh가 php/scripts/test.sh를 호출한다는 문서의
    주장이 실제 스크립트 내용과 맞는지 확인한다(0430)."""
    php_qa_contents = PHP_QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "test.sh" in php_qa_contents
