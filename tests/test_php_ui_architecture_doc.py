"""PHP UI 아키텍처 문서를 검증한다."""

from pathlib import Path


DOC_PATH = Path(__file__).parent.parent / "docs" / "php-ui-architecture.md"

REQUIRED_HEADINGS = [
    "# PHP UI Architecture",
    "## 목적",
    "## 서버 렌더링 기본값",
    "## 템플릿 경계",
    "## 정적 Asset 정책",
    "## 보안 기준",
    "## 후속 태스크 연결",
    "## 관련 문서",
]


def test_php_ui_architecture_doc_exists():
    """0521 UI 아키텍처 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_php_ui_architecture_doc_has_required_headings():
    """후속 UI 태스크가 참조할 필수 섹션을 고정한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    for heading in REQUIRED_HEADINGS:
        assert heading in content


def test_php_ui_architecture_doc_sets_server_rendered_no_build_default():
    """서버 렌더링, 정적 asset, no-build 기본값을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "PHP 서버 렌더링" in content
    assert "CSS와 JavaScript는 정적 asset" in content
    assert "no-build" in content
    assert "Node 기반 mandatory build" in content


def test_php_ui_architecture_doc_defines_template_boundary():
    """템플릿 계층이 DB/권한/도메인 규칙을 소유하지 않는다고 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "view model" in content
    assert "PDO query 실행" in content
    assert "권한 판정" in content
    assert "도메인 규칙" in content


def test_php_ui_architecture_doc_mentions_security_baseline():
    """escaping과 CSRF form 확장 지점을 UI 기준에 포함한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "escaping" in content
    assert "raw HTML" in content
    assert "CSRF token" in content
