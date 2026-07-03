"""UI route parity matrix 문서를 검증한다."""

from pathlib import Path


DOC_PATH = Path(__file__).parent.parent / "docs" / "ui-route-parity-matrix.md"

REQUIRED_HEADINGS = [
    "# UI Route Parity Matrix",
    "## 배경",
    "## 정본(Source of Truth)",
    "## 라우트 상태 정의 (5단계)",
    "## UI와 API 라우트의 구분",
    "## 라우트 parity matrix",
    "## Phase D 진행에 따른 갱신 계획",
    "## 이 표를 최신으로 유지하는 방법",
    "## 관련 문서",
]


def test_ui_route_parity_matrix_doc_exists():
    """0562 UI route parity matrix 문서가 존재한다."""
    assert DOC_PATH.is_file(), f"{DOC_PATH}가 없습니다"


def test_ui_route_parity_matrix_doc_has_required_headings():
    """후속 UI 태스크가 참조할 필수 섹션을 고정한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"'{heading}' 섹션이 없습니다"


def test_ui_route_parity_matrix_doc_defines_status_levels():
    """라우트 상태 5단계를 정의한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    status_levels = [
        "not-started",
        "placeholder",
        "python-only",
        "parity",
        "canonical-php",
    ]

    for level in status_levels:
        assert level in content, f"'{level}' 상태가 정의되지 않았습니다"


def test_ui_route_parity_matrix_doc_distinguishes_ui_and_api_routes():
    """UI와 API 라우트의 구분을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "## UI와 API 라우트의 구분" in content
    assert "UI 라우트 (서버 렌더링 HTML)" in content
    assert "API 라우트 (JSON 응답)" in content
    assert "인프라 라우트 (모니터링/진단)" in content


def test_ui_route_parity_matrix_doc_mentions_source_of_truth():
    """Python과 PHP의 정본 소스를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "src/app/main.py" in content
    assert "src/modules/*/router.py" in content
    assert "php/public/index.php" in content
    assert "php/src/Http/" in content


def test_ui_route_parity_matrix_doc_establishes_php_as_canonical():
    """최종적으로 PHP 라우트가 canonical임을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "canonical-php" in content
    assert "PHP 라우트가 canonical" in content or "PHP 라우트" in content
