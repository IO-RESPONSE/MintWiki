"""Shared hosting 성능 체크리스트 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "shared-hosting-performance-checklist.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return " ".join(_content().split())


def test_shared_hosting_performance_checklist_doc_exists():
    """0659 shared hosting 성능 체크리스트 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_shared_hosting_performance_checklist_defines_opcode_cache_checks():
    """OPcache 활성화와 배포 후 갱신 확인 기준을 명시한다."""
    content = _unwrapped_content()

    assert "Opcode Cache 체크리스트" in content
    assert "`opcache.enable=1`" in content
    assert "`opcache.validate_timestamps=1`" in content
    assert "`opcache.revalidate_freq`" in content
    assert "OPcache reset" in content
    assert "version/build marker" in content


def test_shared_hosting_performance_checklist_defines_static_cache_checks():
    """정적 asset 캐시와 HTML 캐시 분리 기준을 명시한다."""
    content = _unwrapped_content()

    assert "Static Cache 체크리스트" in content
    assert "`php/public/assets/`" in content
    assert "rewrite를 우회" in content
    assert "`Cache-Control: public`" in content
    assert "HTML 응답은 static cache 대상이 아니" in content
    assert "version 값" in content


def test_shared_hosting_performance_checklist_defines_db_index_checks():
    """핵심 shared hosting 조회 경로의 DB index 점검 기준을 명시한다."""
    content = _unwrapped_content()

    assert "DB Index 체크리스트" in content
    assert "unique 또는 lookup index" in content
    assert "revision 작성 시간과 문서 ID" in content
    assert "session token lookup index" in content
    assert "job polling runner" in content
    assert "`EXPLAIN`" in content


def test_shared_hosting_performance_checklist_links_related_docs():
    """관련 hosting, cache, DB 성능 문서와 연결한다."""
    content = _content()

    for reference in [
        "shared-hosting-target-baseline.md",
        "php-static-asset-serving.md",
        "php-ui-cache-header-policy.md",
        "php-ui-performance-budget.md",
        "db-web-hosting-constraints.md",
        "shared-hosting-migration-policy.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
