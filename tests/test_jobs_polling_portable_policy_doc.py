"""jobs polling portable policy 문서를 검증한다."""

from pathlib import Path


DOC_PATH = Path(__file__).parent.parent / "docs" / "jobs-polling-portable-policy.md"


def test_jobs_polling_portable_policy_doc_exists():
    """0516 정책 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_policy_excludes_skip_locked_as_default():
    """기본 polling 경로에서 SKIP LOCKED를 제외한다고 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "SKIP LOCKED" in content
    assert "기본 구현에서 제외" in content or "기본값" in content


def test_policy_defines_candidate_query_and_claim_update():
    """후보 조회와 조건부 claim update를 모두 정의한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "SELECT id" in content
    assert "WHERE status = 'queued'" in content
    assert "UPDATE job" in content
    assert "attempts = attempts + 1" in content
    assert "영향 행 수" in content


def test_policy_defines_terminal_and_retry_transitions():
    """성공, 재시도, dead-letter 전이 규칙을 정의한다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "status = 'succeeded'" in content
    assert "status = 'dead_letter'" in content
    assert "status = 'queued'" in content
    assert "attempts < max_attempts" in content


def test_policy_mentions_shared_hosting_constraints():
    """shared hosting 제약과 짧은 runner 실행 모델을 다룬다."""
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "shared hosting" in content
    assert "cron" in content or "웹 트리거" in content
    assert "long-running daemon" in content


def test_jobs_plan_links_to_polling_policy():
    """기존 jobs portable plan이 0516 정책 문서를 참조한다."""
    plan_path = Path(__file__).parent.parent / "docs" / "jobs-portable-repository-plan.md"
    content = plan_path.read_text(encoding="utf-8")

    assert "jobs-polling-portable-policy.md" in content
