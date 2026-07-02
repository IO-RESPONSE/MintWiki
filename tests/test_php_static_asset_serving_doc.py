"""PHP 정적 자산 제공 문서를 검증한다."""

from pathlib import Path


DOC_PATH = Path(__file__).parent.parent / "docs" / "php-static-asset-serving.md"


REQUIRED_HEADINGS = [
    "# PHP Static Asset Serving",
    "## 목적",
    "## 디렉터리 구조",
    "## 웹 서버 직접 제공",
    "## no-build 기본값",
    "## 캐시와 버전",
    "## 보안 기준",
    "## 후속 태스크 연결",
    "## 관련 문서",
]


def test_php_static_asset_serving_doc_exists():
    """0524 정적 자산 제공 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_php_static_asset_serving_doc_has_required_headings():
    """후속 asset 태스크가 참조할 필수 섹션을 고정한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    for heading in REQUIRED_HEADINGS:
        assert heading in content


def test_php_static_asset_serving_doc_uses_public_document_root():
    """shared hosting public 문서 루트 구조를 기준으로 한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "php/public/" in content
    assert "assets/" in content
    assert "문서 루트" in content


def test_php_static_asset_serving_doc_bypasses_front_controller():
    """정적 asset은 웹 서버가 직접 제공하고 front controller를 거치지 않는다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "front controller" in content
    assert "index.php" in content
    assert "직접 제공" in content


def test_php_static_asset_serving_doc_keeps_no_build_default():
    """no-build 기본값과 제외 항목을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "no-build" in content
    assert "Node 기반 mandatory build" in content


def test_php_static_asset_serving_doc_defers_cache_and_integrity():
    """cache header와 integrity 정책을 후속 태스크로 미룬다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "0577" in content
    assert "0578" in content
    assert "0606" in content
