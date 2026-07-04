"""Shared hosting 제공자별 샘플 체크리스트 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "shared-hosting-provider-checklist-samples.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return " ".join(_content().split())


def test_shared_hosting_provider_checklist_samples_doc_exists():
    """0665 제공자별 샘플 체크리스트 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_shared_hosting_provider_checklist_samples_cover_required_providers():
    """cPanel, Plesk, plain FTP 기준 샘플을 모두 포함한다."""
    content = _content()

    assert "cPanel 샘플 체크리스트" in content
    assert "Plesk 샘플 체크리스트" in content
    assert "Plain FTP 샘플 체크리스트" in content


def test_shared_hosting_provider_checklist_samples_cover_cpanel_basics():
    """cPanel 샘플이 PHP, DB, document root, installer 확인을 포함한다."""
    content = _unwrapped_content()

    assert "MultiPHP Manager" in content
    assert "MySQL Databases" in content
    assert "document root가 `php/public/`" in content
    assert "File Manager" in content
    assert "`storage/installer/install.lock`" in content


def test_shared_hosting_provider_checklist_samples_cover_plesk_basics():
    """Plesk 샘플이 PHP Settings, DB, 로그, 공개 경로 확인을 포함한다."""
    content = _unwrapped_content()

    assert "Hosting Settings" in content
    assert "PHP Settings" in content
    assert "Databases 화면" in content
    assert "Logs 화면" in content
    assert "`composer.json`, `composer.lock`, `vendor/`, `config/`, `storage/` URL 직접 접근" in content


def test_shared_hosting_provider_checklist_samples_cover_plain_ftp_basics():
    """plain FTP 샘플이 with_vendor, 업로드 순서, 권한 확인을 포함한다."""
    content = _unwrapped_content()

    assert "plain FTP 계정은 SSH, Composer, 심볼릭 링크 전환을 사용할 수 없다고 가정" in content
    assert "`with_vendor` 패키지" in content
    assert "업로드 순서는 `php/vendor/`, `php/src/`, `php/config/*.sample`, `db/schema/`, `storage/`, `php/public/` 순서" in content
    assert "FTP 클라이언트의 size 비교 또는 checksum 기능" in content
    assert "임시 `777` 권한은 운영 전 되돌렸다" in content


def test_shared_hosting_provider_checklist_samples_link_related_docs():
    """관련 shared hosting 배포 문서와 연결한다."""
    content = _content()

    for reference in [
        "shared-hosting-target-baseline.md",
        "shared-hosting-qa-checklist.md",
        "composer-hosting-deployment.md",
        "no-composer-hosting-deployment.md",
        "public-docroot-policy.md",
        "writable-directories-policy.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
