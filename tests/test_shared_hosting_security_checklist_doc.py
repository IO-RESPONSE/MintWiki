"""Shared hosting 보안 체크리스트 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "shared-hosting-security-checklist.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return " ".join(_content().split())


def test_shared_hosting_security_checklist_doc_exists():
    """0658 shared hosting 보안 체크리스트 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_shared_hosting_security_checklist_defines_public_path_checks():
    """public path와 비공개 경로 분리 기준을 명시한다."""
    content = _unwrapped_content()

    assert "Public Path 체크리스트" in content
    assert "document root는 `php/public/` 하나만" in content
    assert "`php/src/`, `php/config/`, `php/vendor/`, `db/`, `docs/`, `tests/`, `storage/`는 document root 밖" in content
    assert "403 또는 404" in content
    assert "front controller를 거쳐 권한 검사" in content


def test_shared_hosting_security_checklist_defines_config_checks():
    """config 파일과 민감값 노출 방지 기준을 명시한다."""
    content = _unwrapped_content()

    assert "Config 체크리스트" in content
    assert "실제 DB 자격증명" in content
    assert "document root 밖" in content
    assert "`chmod 640`" in content
    assert "`chmod 600`" in content
    assert "DB 비밀번호, DSN 전체 문자열, API 키" in content


def test_shared_hosting_security_checklist_defines_installer_checks():
    """installer 검사와 완료 후 차단 기준을 명시한다."""
    content = _unwrapped_content()

    assert "Installer 체크리스트" in content
    assert "installer requirement check" in content
    assert "`storage/cache/`, `storage/uploads/`, `storage/logs/`" in content
    assert "`storage/installer/install.lock`" in content
    assert "installation_already_complete" in content
    assert "수동 lock file 삭제" in content


def test_shared_hosting_security_checklist_defines_permission_checks():
    """permissions 최소 권한과 777 금지를 명시한다."""
    content = _unwrapped_content()

    assert "Permissions 체크리스트" in content
    assert "읽기 전용 배포 파일" in content
    assert "`chmod 750`" in content
    assert "PHP 스크립트를 실행 가능한 상태로 두지 않는다" in content
    assert "777" in content


def test_shared_hosting_security_checklist_links_related_docs():
    """관련 public path, config, installer, permissions 문서와 연결한다."""
    content = _content()

    for reference in [
        "public-docroot-policy.md",
        "config-file-permission-policy.md",
        "installer-lock-file-policy.md",
        "writable-directories-policy.md",
        "php-runtime-security-baseline.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
