"""Shared hosting QA 체크리스트 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "shared-hosting-qa-checklist.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return " ".join(_content().split())


def test_shared_hosting_qa_checklist_doc_exists():
    """0660 shared hosting QA 체크리스트 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_shared_hosting_qa_checklist_covers_installation():
    """설치 QA가 document root, installer, lock file을 포함한다."""
    content = _unwrapped_content()

    assert "설치 QA" in content
    assert "document root가 `php/public/`" in content
    assert "installer requirement check" in content
    assert "`storage/cache/`, `storage/uploads/`, `storage/logs/`" in content
    assert "`storage/installer/install.lock`" in content
    assert "installation_already_complete" in content


def test_shared_hosting_qa_checklist_covers_upgrade():
    """업그레이드 QA가 릴리스 정합성, schema, cache clear를 포함한다."""
    content = _unwrapped_content()

    assert "업그레이드 QA" in content
    assert "`php/vendor/`, `php/composer.lock`이 같은 릴리스" in content
    assert "현재 schema version과 필요한 schema version" in content
    assert "필요한 마이그레이션" in content
    assert "PHP opcode cache" in content
    assert "Class not found" in content


def test_shared_hosting_qa_checklist_covers_rollback():
    """Rollback QA가 DB 호환성과 이전 릴리스 복원을 포함한다."""
    content = _unwrapped_content()

    assert "Rollback QA" in content
    assert "실패한 릴리스 식별자" in content
    assert "additive 변경" in content
    assert "destructive migration" in content
    assert "이전 릴리스의 `php/src/`, `php/public/`, `php/vendor/`, `php/composer.lock`" in content
    assert "운영 설정 파일, 사용자 업로드, export 파일" in content


def test_shared_hosting_qa_checklist_covers_forms_and_admin():
    """Forms와 admin QA가 CSRF, 오류 표시, diagnostics, 민감값 비노출을 포함한다."""
    content = _unwrapped_content()

    assert "Forms QA" in content
    assert "CSRF token" in content
    assert "role=\"alert\"" in content
    assert "HTML escape" in content
    assert "Admin QA" in content
    assert "`/admin/diagnostics`" in content
    assert "DB 비밀번호, DSN 전체 문자열, 세션 ID, 쿠키, API key" in content


def test_shared_hosting_qa_checklist_links_related_docs():
    """관련 shared hosting, UI, installer 문서와 연결한다."""
    content = _content()

    for reference in [
        "shared-hosting-security-checklist.md",
        "shared-hosting-upgrade-procedure.md",
        "shared-hosting-rollback-procedure.md",
        "shared-hosting-migration-policy.md",
        "php-ui-manual-qa-script.md",
        "php-ui-phase-qa-checklist.md",
        "installer-lock-file-policy.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
