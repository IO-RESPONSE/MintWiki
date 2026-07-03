"""Export directory 정책 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "export-directory-policy.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return _content().replace("\n  ", " ").replace("\n", " ")


def test_export_directory_policy_doc_exists():
    """0639 export directory 정책 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_export_directory_policy_doc_keeps_exports_outside_docroot():
    """export 파일은 public 밖 저장을 기본으로 한다."""
    content = _unwrapped_content()

    assert "기본적으로 public document root 밖에 저장" in content
    assert "`storage/exports/`" in content
    assert "`php/public/`, `public/`, `public_html/` 바로 아래에는 export 파일을 저장하지 않는다" in content
    assert "웹 서버 직접 접근을 금지" in content


def test_export_directory_policy_doc_separates_export_storage():
    """export 저장소를 다른 런타임 쓰기 경로와 분리한다."""
    content = _content()

    assert "storage/uploads/" in content
    assert "storage/cache/" in content
    assert "storage/logs/" in content
    assert "독립된 디렉터리" in content
    assert "심볼릭 링크" in content


def test_export_directory_policy_doc_defines_download_boundary():
    """export 다운로드는 인증된 front controller 경로로만 허용한다."""
    content = _content()

    assert "public/index.php" in content
    assert "관리자 권한" in content
    assert "스트리밍" in content
    assert "정적 파일로 취급하지 않는다" in content


def test_export_directory_policy_doc_defines_installer_checks():
    """installer requirement check가 확인할 export 디렉터리 조건을 고정한다."""
    content = _unwrapped_content()

    assert "installer requirement check" in content
    assert "디렉터리이며 document root 밖" in content
    assert "쓰기, 읽기, 삭제" in content
    assert "임시 export 파일" in content
    assert "심볼릭 링크가 아니다" in content


def test_export_directory_policy_doc_links_related_docs():
    """관련 호스팅/권한 문서와 연결한다."""
    content = _content()

    for reference in [
        "shared-hosting-target-baseline.md",
        "public-docroot-policy.md",
        "writable-directories-policy.md",
        "config-file-permission-policy.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
