"""Writable directories 정책 문서를 검증한다."""

from pathlib import Path


DOC_PATH = Path(__file__).parent.parent / "docs" / "writable-directories-policy.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_writable_directories_policy_doc_exists():
    """0626 writable directories 정책 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_writable_directories_policy_doc_separates_runtime_directories():
    """cache, uploads, logs 쓰기 경로를 서로 분리한다."""
    content = _content()

    assert "storage/cache/" in content
    assert "storage/uploads/" in content
    assert "storage/logs/" in content
    assert "심볼릭 링크" in content
    assert "독립적으로" in content


def test_writable_directories_policy_doc_keeps_storage_outside_docroot():
    """쓰기 디렉터리는 공개 document root 밖에 둔다."""
    content = _content()

    assert "document root 밖" in content
    assert "php/public/" in content
    assert "웹 서버 직접 접근을 금지" in content


def test_writable_directories_policy_doc_defines_installer_checks():
    """후속 installer requirement check가 확인할 조건을 고정한다."""
    content = _content()

    assert "installer requirement check" in content
    assert "디렉터리 여부" in content
    assert "쓰기 가능 여부" in content
    assert "읽기 가능 여부" in content
    assert "임시 파일" in content


def test_writable_directories_policy_doc_defines_permission_baseline():
    """shared hosting용 최소 권한 기준과 777 금지를 명시한다."""
    content = _content()

    assert "chmod 750 storage/cache" in content
    assert "chmod 750 storage/uploads" in content
    assert "chmod 750 storage/logs" in content
    assert "777" in content
    assert "경고" in content


def test_writable_directories_policy_doc_links_related_security_docs():
    """관련 보안/호스팅 문서와 연결한다."""
    content = _content()

    assert "shared-hosting-target-baseline.md" in content
    assert "public-docroot-policy.md" in content
    assert "config-file-permission-policy.md" in content
    assert "php-runtime-security-baseline.md" in content
