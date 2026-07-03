"""Cookie security 정책 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "cookie-security-policy.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return _content().replace("\n  ", " ").replace("\n", " ")


def test_cookie_security_policy_doc_exists():
    """0634 cookie 보안 정책 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_cookie_security_policy_doc_defines_required_cookie_flags():
    """Secure, HttpOnly, SameSite 기준을 모두 명시한다."""
    content = _content()

    assert "`Secure`" in content
    assert "`HttpOnly`" in content
    assert "`SameSite`" in content
    assert "`Secure=true`" in content
    assert "`HttpOnly=true`" in content
    assert "`SameSite=Lax`" in content


def test_cookie_security_policy_doc_limits_secure_exceptions():
    """운영 배포는 HTTPS와 Secure 쿠키를 기본으로 삼는다."""
    content = _unwrapped_content()

    assert "운영 배포는 HTTPS를 전제로" in content
    assert "HTTPS가 아니면 운영 설치 통과로 취급하지 않는다" in content
    assert "로컬 개발이나 CLI 테스트" in content
    assert "운영 설정 파일에 저장하지 않는다" in content


def test_cookie_security_policy_doc_defines_samesite_policy():
    """SameSite 기본값과 None/Strict 판단 기준을 고정한다."""
    content = _content()

    assert "기본값은 `SameSite=Lax`" in content
    assert "`SameSite=None`" in content
    assert "반드시 `Secure=true`와 함께" in content
    assert "`SameSite=Strict`" in content
    assert "패키지 기본값으로 쓰지 않는다" in content


def test_cookie_security_policy_doc_defines_installer_checks():
    """installer requirement check가 확인할 쿠키 조건을 고정한다."""
    content = _unwrapped_content()

    assert "installer requirement check" in content
    assert "public base URL이 HTTPS" in content
    assert "속성을 명시해서 쿠키를" in content
    assert "발급할 수 있는지 확인" in content
    assert "개발 환경 예외" in content


def test_cookie_security_policy_doc_links_related_security_docs():
    """관련 세션·런타임·호스팅 문서와 연결한다."""
    content = _content()

    for reference in [
        "shared-hosting-session-policy.md",
        "php-runtime-security-baseline.md",
        "public-docroot-policy.md",
        "shared-hosting-target-baseline.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
