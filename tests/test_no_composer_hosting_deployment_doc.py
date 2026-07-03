"""Composer 없는 호스팅 배포 문서를 검증한다."""

from pathlib import Path


DOC_PATH = (
    Path(__file__).parent.parent / "docs" / "no-composer-hosting-deployment.md"
)


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_no_composer_hosting_deployment_doc_exists():
    """0642 Composer 없는 호스팅 배포 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_no_composer_hosting_deployment_doc_defines_vendor_preupload():
    """vendor 사전 업로드 절차와 포함 파일을 명시한다."""
    content = _content()

    assert "Composer를 실행할 수 없는 공용 웹호스팅" in content
    assert "php/vendor/" in content
    assert "php/vendor/autoload.php" in content
    assert "php/composer.lock" in content
    assert "vendor/`를 먼저 업로드" in content


def test_no_composer_hosting_deployment_doc_defines_package_option():
    """with_vendor 패키지 선택 기준을 고정한다."""
    content = _content()

    assert "with_vendor" in content
    assert "without_vendor" in content
    assert "php/deployment-package-manifest.json" in content
    assert "SSH 없음 또는 Composer 금지" in content
    assert "호스팅 PHP 버전" in content


def test_no_composer_hosting_deployment_doc_preserves_public_docroot_boundary():
    """vendor가 document root 밖에 있어야 함을 명시한다."""
    content = _content()

    assert "document root 밖" in content
    assert "php/public/" in content
    assert "vendor/` URL 직접 접근" in content
    assert "403 또는 404" in content


def test_no_composer_hosting_deployment_doc_links_related_docs():
    """관련 호스팅, 배포, 마이그레이션 문서와 연결한다."""
    content = _content()

    assert "shared-hosting-target-baseline.md" in content
    assert "php-ui-deployment-checklist.md" in content
    assert "shared-hosting-migration-policy.md" in content
    assert "public-docroot-policy.md" in content
