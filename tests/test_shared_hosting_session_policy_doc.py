"""Shared hosting session 정책 문서를 검증한다."""

from pathlib import Path


DOC_PATH = (
    Path(__file__).parent.parent / "docs" / "shared-hosting-session-policy.md"
)


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_shared_hosting_session_policy_doc_exists():
    """0632 shared hosting session 정책 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_shared_hosting_session_policy_doc_defines_three_storage_options():
    """PHP 기본 세션, 파일 기반 세션, DB 기반 세션 선택지를 모두 둔다."""
    content = _content()

    assert "PHP 기본 세션" in content
    assert "파일 기반 세션" in content
    assert "DB 기반 세션" in content
    assert "storage/sessions/" in content
    assert "user_session" in content


def test_shared_hosting_session_policy_doc_defines_selection_order():
    """shared hosting 기본 선택 순서와 DB 선택 조건을 고정한다."""
    content = _content()

    assert "PHP 기본 세션을 먼저 검사" in content
    assert "실패하면 파일 기반 세션" in content
    assert "DB 기반 세션은" in content
    assert "여러 웹 노드" in content
    assert "호스팅사의 임의 파일 정리 정책" in content


def test_shared_hosting_session_policy_doc_defines_installer_checks():
    """installer requirement check가 검사할 세션 조건을 명시한다."""
    content = _content()

    assert "installer requirement check" in content
    assert "session.save_handler" in content
    assert "session.save_path" in content
    assert "document root 밖" in content
    assert "읽기 가능 여부" in content
    assert "쓰기 가능 여부" in content
    assert "삭제 가능 여부" in content
    assert "PDO MariaDB" in content


def test_shared_hosting_session_policy_doc_preserves_security_boundaries():
    """세션 보안 공통 기준과 도메인 계층 분리를 명시한다."""
    content = _content()

    assert "로그인 성공 시 세션 ID를 재발급" in content
    assert "Session.expires_at" in content
    assert "php/src/Modules/" in content
    assert "어댑터 계층" in content
    assert "비밀번호" in content


def test_shared_hosting_session_policy_doc_links_related_docs():
    """관련 보안, 호스팅, 저장소 계약 문서와 연결한다."""
    content = _content()

    assert "php-runtime-security-baseline.md" in content
    assert "writable-directories-policy.md" in content
    assert "shared-hosting-target-baseline.md" in content
    assert "repository-port-contracts.md" in content
