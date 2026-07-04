"""`docs/iowiki-shared-hosting-porting-log.md`가 0671 태스크의 acceptance
criteria(docroot 확인, index.php 백업, phpinfo 진단, 배포/설치/스모크
테스트, 설치 후 점검, 비밀번호 미기록)를 실제로 다루고 있으며, 문서가
가리키는 스크립트/문서가 실제로 존재하는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "iowiki-shared-hosting-porting-log.md"

REQUIRED_HEADINGS = [
    "## 목적과 범위",
    "## 1. FTP 루트 확인 결과",
    "## 2. phpinfo 진단 결과 요약",
    "## 3. 디렉터리 배치 결정 (이 계정 전용)",
    "## 4. 배포 절차와 사용 스크립트",
    "## 5. 실행 상태",
    "## 6. 설치 후 점검 (실행 예정 절차)",
    "## 관련 문서",
]

REFERENCED_SCRIPTS = [
    "php/scripts/ftp-deploy.sh",
    "php/scripts/phpinfo-probe.sh",
    "php/scripts/live-http-smoke-test.sh",
    "php/scripts/build-package.sh",
]

REFERENCED_DOCS = [
    "shared-hosting-provider-checklist-samples.md",
    "public-docroot-policy.md",
    "config-file-permission-policy.md",
    "installer-lock-file-policy.md",
    "shared-hosting-security-checklist.md",
    "shared-hosting-target-baseline.md",
    "mariadb-compatibility-matrix.md",
    "php-db-config.md",
    "writable-directories-policy.md",
    "shared-hosting-rollback-procedure.md",
    "final-python-to-php-cutover-plan.md",
]


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_porting_log_doc_exists():
    assert DOC_PATH.is_file()


def test_porting_log_doc_has_required_sections():
    content = _doc_text()
    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_porting_log_doc_references_existing_scripts():
    content = _doc_text()
    for script in REFERENCED_SCRIPTS:
        assert script in content, f"missing script reference: {script}"
        assert (REPO_ROOT / script).is_file(), f"referenced script missing: {script}"


def test_porting_log_doc_references_existing_docs():
    content = _doc_text()
    for doc in REFERENCED_DOCS:
        assert doc in content, f"missing doc reference: {doc}"
        assert (REPO_ROOT / "docs" / doc).is_file(), f"referenced doc missing: {doc}"


def test_porting_log_doc_records_ftp_root_findings():
    content = _doc_text()
    assert "iowiki.iwinv.net" in content
    assert "limits/" in content
    assert "public_html/" in content


def test_porting_log_doc_records_phpinfo_findings():
    content = _doc_text()
    assert "8.4.16" in content
    assert "pdo_mysql" in content
    assert "/home1/iowiki/public_html" in content


def test_porting_log_doc_never_contains_a_real_secret_looking_value():
    """비밀번호/자격증명이 실수로 기록되지 않았는지 최소한의 안전장치로 확인한다."""
    content = _doc_text().lower()
    for forbidden in ["password:", "password=", "ftp_password=iowiki", "pwd:"]:
        assert forbidden not in content, f"possible credential leak: {forbidden}"


def test_porting_log_doc_marks_credential_dependent_steps_as_pending():
    """실제 자격증명 없이 완료했다고 거짓 기록하지 않아야 한다."""
    content = _doc_text()
    assert "대기" in content
    assert "자격증명" in content
