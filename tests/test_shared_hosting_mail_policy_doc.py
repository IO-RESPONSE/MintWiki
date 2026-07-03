"""Shared hosting mail 정책 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "shared-hosting-mail-policy.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return _content().replace("\n  ", " ").replace("\n", " ")


def test_shared_hosting_mail_policy_doc_exists():
    """0636 shared hosting mail 정책 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_shared_hosting_mail_policy_doc_defines_delivery_options():
    """SMTP, PHP mail 함수, 발송 비활성화 선택지를 모두 둔다."""
    content = _unwrapped_content()

    assert "인증 SMTP" in content
    assert "PHP `mail()`" in content
    assert "발송 비활성화" in content
    assert "SMTP를 먼저 검사" in content
    assert "`mail()`을 제한적 대안" in content


def test_shared_hosting_mail_policy_doc_defines_smtp_requirements():
    """SMTP 연결과 자격증명 보호 기준을 명시한다."""
    content = _unwrapped_content()

    assert "SMTP host" in content
    assert "SMTP port" in content
    assert "encryption mode" in content
    assert "username" in content
    assert "password" in content
    assert "TLS 인증서 검증을 끄는 설정은 패키지 기본값으로 제공하지 않는다" in content
    assert "document root 밖의 비공개 설정 파일" in content


def test_shared_hosting_mail_policy_doc_defines_php_mail_limits():
    """PHP mail 함수의 채택 조건과 성공 판정 한계를 고정한다."""
    content = _unwrapped_content()

    assert "`disable_functions`" in content
    assert "`sendmail_path`" in content
    assert "SPF, DKIM, DMARC" in content
    assert "default sender address" in content
    assert "`mail()` 반환값만으로 배달 성공을 판단하지 않는다" in content
    assert "실제 수신함 도착이나 반송 상태를 보장하지 않는다" in content


def test_shared_hosting_mail_policy_doc_defines_installer_checks():
    """installer requirement check가 확인할 메일 조건을 고정한다."""
    content = _unwrapped_content()

    assert "installer requirement check" in content
    assert "host, port, encryption, 인증 정보" in content
    assert "테스트 메일" in content
    assert "`disable_functions`, 발신자 주소를 검사" in content
    assert "운영자 수신 확인을 분리" in content
    assert "제한되는 기능을 표시" in content


def test_shared_hosting_mail_policy_doc_preserves_adapter_boundary():
    """메일 전송 구현이 도메인 계층에 들어가지 않도록 경계를 명시한다."""
    content = _unwrapped_content()

    assert "도메인 계층은" in content
    assert "SMTP 클라이언트" in content
    assert "PHP `mail()` 함수를 직접 호출하지 않는다" in content
    assert "php/src/Modules/" in content
    assert "어댑터 계층" in content


def test_shared_hosting_mail_policy_doc_links_related_docs():
    """관련 호스팅, 설정, 보안 문서와 연결한다."""
    content = _content()

    for reference in [
        "shared-hosting-target-baseline.md",
        "config-file-permission-policy.md",
        "php-runtime-security-baseline.md",
        "writable-directories-policy.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
