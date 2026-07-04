"""Shared hosting cron 정책 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "shared-hosting-cron-policy.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return _content().replace("\n  ", " ").replace("\n", " ")


def test_shared_hosting_cron_policy_doc_exists():
    """0653 shared hosting cron 정책 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_shared_hosting_cron_policy_defines_sync_runner_model():
    """jobs sync runner의 짧은 실행 모델을 명시한다."""
    content = _unwrapped_content()

    assert "jobs sync runner" in content
    assert "30초 이내 종료" in content
    assert "max_execution_time" in content
    assert "long-running daemon" in content
    assert "조건부 `UPDATE`" in content


def test_shared_hosting_cron_policy_defines_cron_path():
    """cron 권장 경로와 운영 기준을 고정한다."""
    content = _unwrapped_content()

    assert "cron job 또는 scheduler" in content
    assert "PHP CLI 경로" in content
    assert "document root 밖" in content
    assert "기본 주기는 5분" in content
    assert "1분 주기" in content


def test_shared_hosting_cron_policy_defines_web_trigger_alternative():
    """cron 없는 호스팅을 위한 web trigger 대안을 둔다."""
    content = _unwrapped_content()

    assert "web trigger" in content
    assert "HTTPS" in content
    assert "runner secret" in content
    assert "토큰 없는 공개 runner endpoint" in content
    assert "query string" in content


def test_shared_hosting_cron_policy_defines_installer_checks():
    """installer가 표시할 cron/web trigger 선택 기준을 명시한다."""
    content = _unwrapped_content()

    assert "installer requirement check" in content
    assert "cron 권장" in content
    assert "기본 5분 주기" in content
    assert "HTTPS, secret, rate limit" in content
    assert "job 처리가 지연될 수 있음" in content


def test_shared_hosting_cron_policy_links_related_docs():
    """관련 jobs, hosting, 보안 문서와 연결한다."""
    content = _content()

    for reference in [
        "jobs-polling-portable-policy.md",
        "shared-hosting-target-baseline.md",
        "config-file-permission-policy.md",
        "php-runtime-security-baseline.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
