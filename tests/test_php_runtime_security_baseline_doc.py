"""`docs/php-runtime-security-baseline.md` 가 태스크 0438 의 목표("PHP
런타임 보안 기준을 문서화한다")와 Notes 요구사항("escaping, session,
upload, path traversal 기준을 둔다")을 실제로 고정하고 있으며, 문서가
근거로 삼는 Python 원본 파일과 PHP 실제 파일 구조가 어긋나지 않는지
확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-runtime-security-baseline.md"
MICRO_JOB_PROMPTS_DOC_PATH = (
    REPO_ROOT / "docs" / "php-db-ui-micro-job-prompts-0351-0670.md"
)

REQUIRED_DOC_HEADINGS = [
    "## 배경: 이 문서 이후 실제 구현을 맡는 후속 태스크",
    "## 1. Escaping 기준",
    "## 2. Session 기준",
    "## 3. Upload 기준",
    "## 4. Path Traversal 기준",
    "## 이 문서가 하지 않는 것",
    "## 관련 문서",
]

FOLLOW_UP_TASK_IDS = [
    "0540",
    "0554",
    "0567",
    "0571",
    "0626",
    "0629",
    "0632",
    "0633",
    "0634",
    "0635",
    "0638",
    "0658",
]


def test_php_runtime_security_baseline_doc_exists():
    """PHP 런타임 보안 기준 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_runtime_security_baseline_doc_has_required_sections():
    """배경, 네 가지 기준(escaping/session/upload/path traversal), 범위
    제외, 관련 문서 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_runtime_security_baseline_doc_covers_four_notes_topics():
    """태스크 Notes 요구사항: "escaping, session, upload, path traversal
    기준을 둔다" — 네 용어 모두 문서 본문에 등장한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for topic in ["escaping", "session", "upload", "path traversal"]:
        assert topic.lower() in content.lower(), f"missing topic: {topic}"


def test_php_runtime_security_baseline_doc_references_python_originals():
    """escaping/session 기준의 이식 원본으로 삼는 Python 파일이 실제로
    존재한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "src/modules/render/escape.py",
        "src/modules/render/url_sanitizer.py",
        "src/modules/user/session.py",
    ]:
        assert reference in content, f"missing python reference: {reference}"
        assert (REPO_ROOT / reference).is_file(), f"missing file: {reference}"


def test_php_runtime_security_baseline_doc_references_existing_php_files():
    """Response::html()/json() 관련 서술이 가리키는 실제 PHP 파일이
    존재한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "php/src/Http/Response.php" in content
    assert (REPO_ROOT / "php" / "src" / "Http" / "Response.php").is_file()


def test_php_runtime_security_baseline_doc_names_follow_up_tasks():
    """이 문서가 실제 구현을 미루는 후속 태스크 번호가 본문과 마이크로잡
    목록 문서 양쪽에 모두 존재한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    micro_job_content = MICRO_JOB_PROMPTS_DOC_PATH.read_text(encoding="utf-8")
    for task_id in FOLLOW_UP_TASK_IDS:
        assert task_id in content, f"missing follow-up task reference: {task_id}"
        assert f"| {task_id} |" in micro_job_content, (
            f"task {task_id} not found in micro job prompts doc"
        )


def test_php_runtime_security_baseline_doc_defers_implementation():
    """이 문서 스스로는 코드를 구현하지 않는다는 범위 제외를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "이 문서의 범위가 아니다" in content
    assert "실제로 작성하지 않는다" in content


def test_php_runtime_security_baseline_doc_references_related_docs():
    """도메인 경계 문서, 코딩 표준 문서, 전략 문서, 마이크로잡 목록
    문서와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-no-framework-domain-rule.md",
        "docs/php-coding-standard.md",
        "docs/php-replacement-strategy.md",
        "docs/shared-hosting-session-policy.md",
        "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
