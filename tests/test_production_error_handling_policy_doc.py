"""Production error handling 정책 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "production-error-handling-policy.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return _content().replace("\n  ", " ").replace("\n", " ")


def test_production_error_handling_policy_doc_exists():
    """0649 production error handling 정책 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_production_error_handling_policy_doc_separates_user_and_log_messages():
    """사용자 메시지와 로그 메시지를 분리하도록 명시한다."""
    content = _unwrapped_content()

    assert "사용자 메시지와 로그 메시지 분리" in content
    assert "두 메시지는 같은 문자열을 공유하지 않는다" in content
    assert "원본 예외 메시지와 stack trace" in content
    assert "사용자 응답에 그대로 넣지 않는다" in content
    assert "request id" in content


def test_production_error_handling_policy_doc_defines_safe_response_shapes():
    """HTML과 JSON production 오류 응답의 안전한 형식을 고정한다."""
    content = _unwrapped_content()

    assert "HTML 요청은 공통 오류 page를 반환" in content
    assert "JSON 요청은 다음 필드를 기본" in content
    assert "\"code\"" in content
    assert "\"message\"" in content
    assert "\"request_id\"" in content
    assert "production 응답에 포함하지" in content


def test_production_error_handling_policy_doc_defines_code_and_status_mapping():
    """error code와 HTTP 상태 코드 매핑 기준을 명시한다."""
    content = _content()

    assert "document.empty_title" in content
    assert "document.duplicate_title" in content
    assert "document.not_found" in content
    assert "http.not_found" in content
    assert "http.forbidden" in content
    assert "http.validation_failed" in content
    assert "app.internal_error" in content


def test_production_error_handling_policy_doc_defines_logging_safety():
    """production 로그에 남길 값과 남기면 안 되는 값을 구분한다."""
    content = _unwrapped_content()

    assert "log level" in content
    assert "HTTP method, path, status code" in content
    assert "예외 class와 마스킹된 원본 메시지" in content
    assert "비밀번호, token, 원문 쿠키, 요청 body, 응답 body는 남기지 않는다" in content
    assert "docs/php-ui-logging-policy.md" in content


def test_production_error_handling_policy_doc_links_related_docs():
    """관련 logging, runtime, error code, config 문서와 연결한다."""
    content = _content()

    for reference in [
        "php-ui-logging-policy.md",
        "php-runtime-security-baseline.md",
        "portable-exception-code-policy.md",
        "config-file-permission-policy.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
